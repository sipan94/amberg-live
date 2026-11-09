"""Business/club area in the app. Uses the website's forms, validation, image processing and
moderation rules – the app is just another way to fill them in."""
from flask import abort, g, jsonify, request
from sqlalchemy import select

from ..extensions import db, limiter
from ..forms.dashboard import EventForm, OfferForm, OrganizationForm
from ..i18n import t
from ..models import WEEKDAYS, Event, Offer, Organization, OrgType
from ..services import editing, moderation
from ..services.images import ImageError, delete_image
from ..utils import recurrence
from . import bind, bp, error, form_errors, login_required, verified_required
from . import serializers as ser

SUBMIT_LIMIT = "30/hour"


def _org() -> Organization | None:
    return db.session.scalar(select(Organization).where(Organization.owner_id == g.api_user.id)
                             .order_by(Organization.id))


def _own(model, item_id: int):
    item = db.session.get(model, item_id)
    if item is None or item.organization.owner_id != g.api_user.id:
        abort(404)  # never reveal other users' items
    return item


def _saved(item, *, is_new: bool, changed: set[str], old_files, serialize):
    db.session.add(item)
    pending = moderation.submit(item, is_new=is_new, changed=changed)
    db.session.commit()
    editing.delete_files(old_files)
    return jsonify(message=t("dashboard.saved_pending") if pending else t("dashboard.saved_live"),
                   pending=pending, item=serialize(item)), 201 if is_new else 200


def _image_error(exc: ImageError, field: str):
    db.session.rollback()
    return error(str(exc), 422, fields={field: [str(exc)]})


@bp.get("/me/overview")
@login_required
def api_overview():
    org = _org()
    events = offers = []
    if org:
        events = db.session.scalars(select(Event).where(Event.organization_id == org.id)
                                    .order_by(Event.start_at.desc())).all()
        offers = db.session.scalars(select(Offer).where(Offer.organization_id == org.id)
                                    .order_by(Offer.valid_from.desc())).all()
    return jsonify(
        user=ser.user(g.api_user, org),
        organization=ser.my_organization(org, WEEKDAYS) if org else None,
        events=[ser.my_event(e) for e in events],
        offers=[ser.my_offer(o) for o in offers],
    )


@bp.get("/me/form-options")
@login_required
def api_form_options():
    """Choices and labels for the app's forms (same texts as the website)."""
    return jsonify(
        categories=[{"id": cid, "name": name} for cid, name in editing.category_choices()],
        recurrence=[{"value": r, "label": t(f"form.recurrence_{r}")} for r in recurrence.RULES],
        org_types=[{"value": OrgType.BUSINESS, "label": t("form.type_business")},
                   {"value": OrgType.CLUB, "label": t("form.type_club")}],
        weekdays=[{"key": d, "label": t("dates.weekday_keys")[d]} for d in WEEKDAYS],
        rights_label=t("form.rights"),
        review_note=t("form.review_note"),
    )


# ---- organization profile -----------------------------------------------------------

@bp.route("/me/organization", methods=["POST", "PUT"])
@verified_required
@limiter.limit(SUBMIT_LIMIT)
def api_save_organization():
    org = _org()
    is_new = org is None
    form = bind(OrganizationForm)
    if not form.validate():
        return form_errors(form)
    org = org or Organization(owner=g.api_user)
    try:
        old_files = editing.fill_organization(org, form)
    except ImageError as exc:
        return _image_error(exc, "logo")
    changed = set() if is_new else moderation.changed_fields(org)
    return _saved(org, is_new=is_new, changed=changed, old_files=old_files,
                  serialize=lambda o: ser.my_organization(o, WEEKDAYS))


# ---- events -----------------------------------------------------------------------------

def _save_event(event: Event | None):
    org = _org()
    if org is None:
        return error(t("dashboard.profile_first"), 409, code="no_profile")
    is_new = event is None
    form = bind(EventForm)
    form.category_id.choices = editing.category_choices()
    if event is not None:
        form.original_start = event.start_at
    if not form.validate():
        return form_errors(form)
    event = event or Event(organization=org)
    try:
        old_files = editing.fill_event(event, form, org)
    except ImageError as exc:
        return _image_error(exc, "image")
    changed = set() if is_new else moderation.changed_fields(event)
    return _saved(event, is_new=is_new, changed=changed, old_files=old_files, serialize=ser.my_event)


@bp.post("/me/events")
@verified_required
@limiter.limit(SUBMIT_LIMIT)
def api_create_event():
    return _save_event(None)


@bp.route("/me/events/<int:event_id>", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def api_event_item(event_id):
    event = _own(Event, event_id)
    if request.method == "GET":
        return jsonify(ser.my_event(event))
    if request.method == "DELETE":
        return _delete(event)
    if not g.api_user.is_verified:
        return error(t("dashboard.verify_first"), 403, code="not_verified")
    return _save_event(event)


# ---- offers -----------------------------------------------------------------------------

def _save_offer(offer: Offer | None):
    org = _org()
    if org is None:
        return error(t("dashboard.profile_first"), 409, code="no_profile")
    is_new = offer is None
    form = bind(OfferForm)
    if not form.validate():
        return form_errors(form)
    offer = offer or Offer(organization=org)
    try:
        old_files = editing.fill_offer(offer, form)
    except ImageError as exc:
        return _image_error(exc, "image")
    changed = set() if is_new else moderation.changed_fields(offer)
    return _saved(offer, is_new=is_new, changed=changed, old_files=old_files, serialize=ser.my_offer)


@bp.post("/me/offers")
@verified_required
@limiter.limit(SUBMIT_LIMIT)
def api_create_offer():
    return _save_offer(None)


@bp.route("/me/offers/<int:offer_id>", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def api_offer_item(offer_id):
    offer = _own(Offer, offer_id)
    if request.method == "GET":
        return jsonify(ser.my_offer(offer))
    if request.method == "DELETE":
        return _delete(offer)
    if not g.api_user.is_verified:
        return error(t("dashboard.verify_first"), 403, code="not_verified")
    return _save_offer(offer)


def _delete(item):
    image = item.image
    db.session.delete(item)
    db.session.commit()
    delete_image(image)
    return jsonify(message=t("dashboard.deleted"))
