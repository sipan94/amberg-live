"""Copy form data into models and back. Shared by the business dashboard and the admin area."""
from sqlalchemy import select

from ..extensions import db
from ..models import WEEKDAYS, Category, Event, Offer, Organization
from ..utils.html import html_to_text, text_to_html
from .geocode import geocode
from .images import ImageError, delete_image, save_image

__all__ = ["ImageError", "fill_organization", "fill_event", "fill_offer",
           "load_organization", "load_event", "load_offer", "category_choices"]


# ---- helpers ----------------------------------------------------------------

def _apply_image(file_field, remove_field, current: str | None, kind: str) -> tuple[str | None, str | None]:
    """Returns (new column value, old file to delete after a successful commit)."""
    upload = file_field.data
    if upload and getattr(upload, "filename", ""):
        return save_image(upload, kind), current
    if remove_field.data and current:
        return None, current
    return current, None


def _update_coordinates(item, old_address: str | None, fallback: Organization | None = None) -> None:
    """Look up lat/lng when the address is new or changed."""
    if item.address == old_address and item.lat is not None:
        return
    item.lat = item.lng = None
    if not item.address:
        return
    if fallback is not None and fallback.address == item.address and fallback.lat is not None:
        item.lat, item.lng = fallback.lat, fallback.lng
        return
    coords = geocode(item.address)
    if coords:
        item.lat, item.lng = coords


def category_choices() -> list[tuple[int, str]]:
    return [(c.id, c.name) for c in db.session.scalars(select(Category).order_by(Category.sort_order))]


# ---- organization -----------------------------------------------------------

def load_organization(form, org: Organization) -> None:
    form.process(obj=org, description=html_to_text(org.description))
    for day in WEEKDAYS:
        getattr(form, f"hours_{day}").data = (org.opening_hours or {}).get(day, "")


def fill_organization(org: Organization, form) -> list[str | None]:
    """Raises ImageError (nothing saved on disk then). Returns old files to delete after commit."""
    old_address = org.address
    org.name = form.name.data
    org.org_type = form.org_type.data
    org.description = text_to_html(form.description.data)
    org.address = form.address.data or None
    org.phone = form.phone.data or None
    org.email = form.email.data or None
    org.website = form.website.data or None
    hours = {d: getattr(form, f"hours_{d}").data for d in WEEKDAYS if getattr(form, f"hours_{d}").data}
    org.opening_hours = hours or None

    before = {org.logo, org.cover_image}
    try:
        org.logo, old_logo = _apply_image(form.logo, form.remove_logo, org.logo, "logo")
        org.cover_image, old_cover = _apply_image(form.cover, form.remove_cover, org.cover_image, "cover")
    except ImageError:
        for path in {org.logo, org.cover_image} - before:  # logo saved before the cover failed
            delete_image(path)
        raise
    _update_coordinates(org, old_address)
    return [old_logo, old_cover]


# ---- event ------------------------------------------------------------------

def load_event(form, event: Event) -> None:
    form.process(
        obj=event, description=html_to_text(event.description),
        start_date=event.start_at.date(), start_time=event.start_at.time(),
        end_date=event.end_at.date() if event.end_at else None,
        end_time=event.end_at.time() if event.end_at else None,
        rights_confirmed=False,
    )


def fill_event(event: Event, form, org: Organization) -> list[str | None]:
    old_address = event.address
    event.title = form.title.data
    event.category_id = form.category_id.data
    event.description = text_to_html(form.description.data)
    event.start_at, event.end_at = form.start_at, form.end_at
    event.recurrence = form.recurrence.data
    event.recurrence_until = form.recurrence_until.data if event.is_recurring else None
    event.location_name = form.location_name.data
    event.address = form.address.data or None
    event.is_free = form.is_free.data
    event.price_info = None if event.is_free else (form.price_info.data or None)
    event.rights_confirmed = True
    event.image, old_image = _apply_image(form.image, form.remove_image, event.image, "event")
    _update_coordinates(event, old_address, fallback=org)
    return [old_image]


# ---- offer ------------------------------------------------------------------

def load_offer(form, offer: Offer) -> None:
    form.process(obj=offer, description=html_to_text(offer.description), rights_confirmed=False)


def fill_offer(offer: Offer, form) -> list[str | None]:
    offer.title = form.title.data
    offer.description = text_to_html(form.description.data)
    offer.valid_from = form.valid_from.data
    offer.valid_until = form.valid_until.data
    offer.rights_confirmed = True
    offer.image, old_image = _apply_image(form.image, form.remove_image, offer.image, "offer")
    return [old_image]


def delete_files(paths) -> None:
    for path in paths:
        delete_image(path)
