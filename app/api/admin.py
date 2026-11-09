"""Admin in the app: review queue, approve/reject, featured/premium, edit, users,
categories, log, statistics. Reuses the same services as the web admin."""
from datetime import datetime, time

from flask import abort, g, jsonify, request
from sqlalchemy import func, select

from .. import billing
from ..extensions import db
from ..forms.admin import CATEGORY_ICONS, CategoryForm, PremiumForm, RejectForm
from ..forms.dashboard import EventForm, OfferForm, OrganizationForm
from ..i18n import t
from ..models import (WEEKDAYS, ApiToken, Category, Event, ModerationAction, ModerationLog, Offer,
                      Organization, Status, User)
from ..services import editing, moderation
from ..services.images import ImageError
from ..services.stats import admin_overview
from . import admin_required, bind, bp, error, form_errors, page_meta
from . import serializers as ser

KINDS = {"event": Event, "offer": Offer, "organization": Organization}
REJECT_PRESETS = ["incomplete", "no_local", "image", "duplicate", "advertising"]


def _item(kind: str, item_id: int):
    model = KINDS.get(kind) or abort(404)
    return db.session.get(model, item_id) or abort(404)


def _admin_item(item) -> dict:
    """An item as the admin sees it: content + owner + moderation state."""
    if isinstance(item, Event):
        data = ser.my_event(item)
    elif isinstance(item, Offer):
        data = ser.my_offer(item)
    else:
        data = ser.my_organization(item, WEEKDAYS)
    org = item if isinstance(item, Organization) else item.organization
    return data | {
        "kind": {Event: "event", Offer: "offer", Organization: "organization"}[type(item)],
        "organization": ser.org_brief(org) | {"status": org.status},
        "owner_email": org.owner.email,
        "submitted_at": ser.iso(item.updated_at),
        "is_premium": org.is_premium,
        "premium_until": ser.iso(org.premium_until),
        "web_url": moderation.public_url(item),
    }


def _pending_counts() -> dict[str, int]:
    return {k: db.session.scalar(select(func.count(m.id)).where(m.status == Status.PENDING)) or 0
            for k, m in KINDS.items()}


@bp.get("/admin/overview")
@admin_required
def api_admin_overview():
    data = admin_overview()
    return jsonify(
        stats=data["stats"],
        pending=_pending_counts(),
        views_total=data["views_total"],
        days=[{"date": d.isoformat(), "views": v} for d, v in data["days"]],
        top_events=[{"slug": e.slug, "title": e.title, "views": e.view_count} for e in data["top_events"]],
        recent=[{"at": ser.iso(r.created_at), "action": t(f"admin.action_{r.action}"), "label": r.target_label}
                for r in data["recent"]],
    )


@bp.get("/admin/queue")
@admin_required
def api_admin_queue():
    kind = request.args.get("kind", "event")
    model = KINDS.get(kind) or abort(404)
    items = db.session.scalars(select(model).where(model.status == Status.PENDING).order_by(model.updated_at)).all()
    return jsonify(kind=kind, counts=_pending_counts(), items=[_admin_item(i) for i in items],
                   reject_presets=[t(f"admin.preset_{p}") for p in REJECT_PRESETS])


@bp.post("/admin/<kind>/<int:item_id>/approve")
@admin_required
def api_admin_approve(kind, item_id):
    item = _item(kind, item_id)
    moderation.approve(item, g.api_user)
    org = item if isinstance(item, Organization) else item.organization
    note = None if org.is_approved else t("admin.org_not_approved")
    return jsonify(message=t("admin.approved", label=getattr(item, "title", None) or item.name), note=note)


@bp.post("/admin/<kind>/<int:item_id>/reject")
@admin_required
def api_admin_reject(kind, item_id):
    item = _item(kind, item_id)
    form = bind(RejectForm)
    if not form.validate():
        return form_errors(form)
    moderation.reject(item, g.api_user, form.reason.data)
    return jsonify(message=t("admin.rejected", label=getattr(item, "title", None) or item.name))


@bp.post("/admin/<kind>/<int:item_id>/feature")
@admin_required
def api_admin_feature(kind, item_id):
    item = _item(kind, item_id)
    if isinstance(item, Organization):
        abort(400)
    item.is_featured = not item.is_featured
    ModerationLog.record(g.api_user, item, ModerationAction.FEATURE if item.is_featured else ModerationAction.UNFEATURE)
    db.session.commit()
    return jsonify(is_featured=item.is_featured)


@bp.post("/admin/organization/<int:item_id>/premium")
@admin_required
def api_admin_premium(item_id):
    org = _item("organization", item_id)
    form = bind(PremiumForm)
    if not form.validate():
        return form_errors(form)
    payload = (request.get_json(silent=True) or {}) if request.is_json else request.form
    if payload.get("action") == "off":
        billing.clear_premium(org, admin=g.api_user)
    else:
        until = datetime.combine(form.until.data, time(23, 59)) if form.until.data else None
        billing.set_premium(org, until, admin=g.api_user)
    db.session.commit()
    return jsonify(is_premium=org.is_premium, premium_until=ser.iso(org.premium_until))


@bp.route("/admin/<kind>/<int:item_id>", methods=["GET", "POST", "PUT", "DELETE"])
@admin_required
def api_admin_item(kind, item_id):
    item = _item(kind, item_id)
    if request.method == "GET":
        return jsonify(_admin_item(item))
    if request.method == "DELETE":
        images = [item.logo, item.cover_image] if isinstance(item, Organization) else [item.image]
        if isinstance(item, Organization):
            images += [e.image for e in item.events] + [o.image for o in item.offers]
        ModerationLog.record(g.api_user, item, ModerationAction.DELETE)
        db.session.delete(item)
        db.session.commit()
        editing.delete_files(images)
        return jsonify(message=t("admin.deleted"))

    # Edit: same forms as the website; admin edits keep the current status.
    form_class = {Event: EventForm, Offer: OfferForm, Organization: OrganizationForm}[type(item)]
    form = bind(form_class)
    if isinstance(item, Event):
        form.category_id.choices = editing.category_choices()
        form.original_start = item.start_at
    form.rights_confirmed.data = True
    if not form.validate():
        return form_errors(form)
    try:
        if isinstance(item, Event):
            old_files = editing.fill_event(item, form, item.organization)
        elif isinstance(item, Offer):
            old_files = editing.fill_offer(item, form)
        else:
            old_files = editing.fill_organization(item, form)
    except ImageError as exc:
        db.session.rollback()
        return error(str(exc), 422)
    ModerationLog.record(g.api_user, item, ModerationAction.EDIT)
    db.session.commit()
    editing.delete_files(old_files)
    return jsonify(message=t("admin.saved"), item=_admin_item(item))


@bp.get("/admin/content/<kind>")
@admin_required
def api_admin_content(kind):
    model = KINDS.get(kind) or abort(404)
    stmt = select(model)
    status = request.args.get("status", "")
    if status in Status.ALL:
        stmt = stmt.where(model.status == status)
    q = " ".join(request.args.get("q", "").split())[:100]
    if q:
        col = model.name if model is Organization else model.title
        stmt = stmt.where(col.icontains(q, autoescape=True))
    order = {Event: Event.start_at.desc(), Offer: Offer.valid_from.desc(), Organization: Organization.name}[model]
    page = db.paginate(stmt.order_by(order), page=request.args.get("seite", 1, type=int), per_page=25, error_out=False)
    return jsonify(items=[_admin_item(i) for i in page.items], **page_meta(page))


@bp.get("/admin/users")
@admin_required
def api_admin_users():
    q = " ".join(request.args.get("q", "").split())[:100]
    stmt = select(User)
    if q:
        stmt = stmt.where(User.email.icontains(q, autoescape=True))
    page = db.paginate(stmt.order_by(User.created_at.desc()), page=request.args.get("seite", 1, type=int),
                       per_page=25, error_out=False)
    return jsonify(items=[{
        "id": u.id, "email": u.email, "role": u.role, "is_admin": u.is_admin, "is_verified": u.is_verified,
        "is_blocked": u.is_blocked, "created_at": ser.iso(u.created_at), "last_login_at": ser.iso(u.last_login_at),
        "organizations": [ser.org_brief(o) | {"status": o.status} for o in u.organizations],
        "is_me": u.id == g.api_user.id,
    } for u in page.items], **page_meta(page))


@bp.post("/admin/users/<int:user_id>/block")
@admin_required
def api_admin_block(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.id == g.api_user.id:
        return error(t("admin.nothing_found"), 400)
    user.is_blocked = not user.is_blocked
    if user.is_blocked:
        ApiToken.revoke_all(user.id)  # log the user out of the app immediately
    ModerationLog.record(g.api_user, user, ModerationAction.BLOCK if user.is_blocked else ModerationAction.UNBLOCK)
    db.session.commit()
    return jsonify(is_blocked=user.is_blocked)


@bp.delete("/admin/users/<int:user_id>")
@admin_required
def api_admin_delete_user(user_id):
    from ..dashboard.routes import erase_user

    user = db.session.get(User, user_id) or abort(404)
    if user.id == g.api_user.id:
        return error(t("admin.nothing_found"), 400)
    ModerationLog.record(g.api_user, user, ModerationAction.DELETE)
    erase_user(user)
    return jsonify(message=t("admin.deleted"))


@bp.get("/admin/categories")
@admin_required
def api_admin_categories():
    rows = db.session.execute(select(Category, func.count(Event.id)).outerjoin(Event)
                              .group_by(Category.id).order_by(Category.sort_order)).all()
    return jsonify(icons=CATEGORY_ICONS, items=[ser.category(c) | {"sort_order": c.sort_order, "events": n}
                                                for c, n in rows])


@bp.route("/admin/categories", methods=["POST"], defaults={"cat_id": None})
@bp.route("/admin/categories/<int:cat_id>", methods=["POST", "PUT", "DELETE"])
@admin_required
def api_admin_category(cat_id):
    cat = (db.session.get(Category, cat_id) or abort(404)) if cat_id else None
    if request.method == "DELETE":
        db.session.delete(cat)
        db.session.commit()
        return jsonify(message=t("admin.deleted"))
    form = bind(CategoryForm, obj=cat)
    if not form.validate():
        return form_errors(form)
    duplicate = db.session.scalar(select(Category).where(Category.name == form.name.data,
                                                         Category.id != (cat.id if cat else 0)))
    if duplicate:
        return error(t("admin.category_exists"), 422, fields={"name": [t("admin.category_exists")]})
    cat = cat or Category()
    form.populate_obj(cat)
    cat.sort_order = cat.sort_order or 0
    db.session.add(cat)
    db.session.commit()
    return jsonify(message=t("admin.saved"), item=ser.category(cat)), 201 if cat_id is None else 200


@bp.get("/admin/log")
@admin_required
def api_admin_log():
    page = db.paginate(select(ModerationLog).order_by(ModerationLog.created_at.desc()),
                       page=request.args.get("seite", 1, type=int), per_page=50, error_out=False)
    return jsonify(items=[{
        "at": ser.iso(e.created_at), "admin": e.admin.email if e.admin else t("admin.system"),
        "action": t(f"admin.action_{e.action}"), "type": t(f"admin.type_{e.target_type}"),
        "label": e.target_label, "reason": e.reason,
    } for e in page.items], **page_meta(page))
