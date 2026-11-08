"""Submission workflow: what happens when businesses create or edit content."""
from flask import current_app, url_for
from sqlalchemy import inspect

from ..models import Event, Offer, Organization, Status
from .mail import send_mail

# Columns that never matter for moderation decisions.
_IGNORED = {"updated_at", "created_at", "view_count", "status", "rejection_reason", "reviewed_at", "slug"}


def changed_fields(obj) -> set[str]:
    """Names of columns changed on `obj` since it was loaded (call before commit)."""
    state = inspect(obj)
    return {col.key for col in state.mapper.column_attrs
            if col.key not in _IGNORED and state.attrs[col.key].history.has_changes()}


def needs_reapproval(item, changed: set[str]) -> bool:
    """Should an already APPROVED item go back to 'pending' after this edit?

    item:    the Event, Offer or Organization being edited (already has the new values)
    changed: column names that changed, e.g. {"title", "start_at", "image"}
    """
    # Text and pictures are where inappropriate content gets in -> review again.
    # Practical updates (time, price, place, category, opening hours) stay live at once,
    # so a business can fix "starts 20:00 instead of 19:00" without disappearing.
    return bool(changed & REVIEW_FIELDS)


REVIEW_FIELDS = {
    "title", "description", "image",                         # events, offers
    "name", "logo", "cover_image", "website", "email",       # organizations
}


def submit(item, *, is_new: bool = False, changed: set[str] | None = None) -> bool:
    """Set the moderation status after create/edit. Returns True if the item is now pending."""
    if is_new or item.status == Status.REJECTED or (
            item.status == Status.APPROVED and needs_reapproval(item, changed or set())):
        item.status = Status.PENDING
        item.rejection_reason = None
        item.reviewed_at = None
        _notify_admin(item, is_new)
        return True
    return False


def _notify_admin(item, is_new: bool) -> None:
    kind = {Event: "Veranstaltung", Offer: "Angebot", Organization: "Profil"}[type(item)]
    label = getattr(item, "title", None) or item.name
    org = item if isinstance(item, Organization) else item.organization
    send_mail(
        current_app.config["ADMIN_EMAIL"],
        f"{'Neu' if is_new else 'Geändert'}: {kind} „{label}“",
        "admin_new_submission",
        kind=kind, label=label, org_name=org.name, is_new=is_new,
        admin_url=url_for("admin.queue", _external=True),
    )
