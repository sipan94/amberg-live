"""Admin area: moderation queue, content management, users, categories, statistics."""
from datetime import datetime, time
from urllib.parse import urlsplit

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from .. import billing
from ..extensions import db
from ..forms.admin import CategoryForm, PremiumForm, RejectForm
from ..forms.auth import SimpleForm
from ..forms.dashboard import EventForm, OfferForm, OrganizationForm
from ..i18n import t
from ..models import (ApiToken, Category, Event, ModerationAction, ModerationLog, Offer, Organization, Status,
                      User)
from ..services import editing, moderation
from ..services.images import ImageError
from ..services.stats import admin_overview
from ..utils.timeutils import now_local
from . import bp

PER_PAGE = 25

# URL name -> model. German URL parts match the rest of the site.
KINDS = {"veranstaltung": Event, "angebot": Offer, "profil": Organization}
KIND_OF = {Event: "veranstaltung", Offer: "angebot", Organization: "profil"}
REJECT_PRESETS = ["incomplete", "no_local", "image", "duplicate", "advertising"]


# ---- access & helpers ---------------------------------------------------------

@bp.before_request
@login_required
def _admins_only():
    if not current_user.is_admin:
        abort(404)  # don't even reveal that an admin area exists


@bp.app_context_processor
def _admin_context():
    if not (current_user.is_authenticated and current_user.is_admin):
        return {}
    return {"admin_pending": lambda: sum(_pending_counts().values())}


@bp.context_processor
def _admin_bp_context():
    return {"pending_counts": _pending_counts(), "kind_of": lambda item: KIND_OF[type(item)],
            "action_form": SimpleForm()}


def _pending_counts() -> dict[str, int]:
    return {kind: db.session.scalar(select(func.count(model.id)).where(model.status == Status.PENDING))
            for kind, model in KINDS.items()}


def get_item(kind: str, item_id: int):
    model = KINDS.get(kind) or abort(404)
    return db.session.get(model, item_id) or abort(404)


def _back(default: str):
    """Return to the page the admin came from (same site only)."""
    target = request.form.get("next") or request.referrer or ""
    parts = urlsplit(target)
    if parts.netloc and parts.netloc != request.host:
        return redirect(default)
    path = parts.path + (f"?{parts.query}" if parts.query else "")
    return redirect(path if path.startswith("/") else default)


def _owner(item) -> User:
    return item.owner if isinstance(item, Organization) else item.organization.owner


def _label(item) -> str:
    return getattr(item, "title", None) or item.name


# ---- overview & statistics ----------------------------------------------------

@bp.get("/")
def index():
    data = admin_overview()
    return render_template("admin/index.html", stats=data["stats"], days=data["days"],
                           views_total=data["views_total"], views_max=max([v for _, v in data["days"]] + [1]),
                           top_events=data["top_events"], recent=data["recent"])


# ---- moderation queue ------------------------------------------------------------

@bp.get("/pruefung")
def queue():
    counts = _pending_counts()
    kind = request.args.get("typ")
    if kind not in KINDS:  # open the first tab that has something waiting
        kind = next((k for k, n in counts.items() if n), "veranstaltung")
    model = KINDS[kind]
    items = db.session.scalars(select(model).where(model.status == Status.PENDING)
                               .order_by(model.updated_at)).all()  # oldest first: fair queue
    return render_template("admin/queue.html", kind=kind, items=items, reject_form=RejectForm(),
                           presets=REJECT_PRESETS)


@bp.post("/<kind>/<int:item_id>/freigeben")
def approve(kind, item_id):
    item = get_item(kind, item_id)
    if not SimpleForm().validate_on_submit():
        abort(400)
    moderation.approve(item, current_user)
    flash(t("admin.approved", label=_label(item)), "success")
    if not isinstance(item, Organization) and not item.organization.is_approved:
        flash(t("admin.org_not_approved"), "info")
    return _back(url_for("admin.queue", typ=kind))


@bp.post("/<kind>/<int:item_id>/ablehnen")
def reject(kind, item_id):
    item = get_item(kind, item_id)
    form = RejectForm()
    if not form.validate_on_submit():
        flash(" ".join(str(e) for e in form.reason.errors) or t("admin.reason_missing"), "error")
        return _back(url_for("admin.queue", typ=kind))
    moderation.reject(item, current_user, form.reason.data)
    flash(t("admin.rejected", label=_label(item)), "success")
    return _back(url_for("admin.queue", typ=kind))


@bp.post("/<kind>/<int:item_id>/hervorheben")
def toggle_featured(kind, item_id):
    item = get_item(kind, item_id)
    if isinstance(item, Organization) or not SimpleForm().validate_on_submit():
        abort(400)
    item.is_featured = not item.is_featured
    ModerationLog.record(current_user, item,
                         ModerationAction.FEATURE if item.is_featured else ModerationAction.UNFEATURE)
    db.session.commit()
    return _back(url_for("admin.content", kind=kind))


@bp.post("/profil/<int:item_id>/premium")
def premium(item_id):
    org = get_item("profil", item_id)
    form = PremiumForm()
    if not form.validate_on_submit():
        abort(400)
    if request.form.get("action") == "off":
        billing.clear_premium(org, admin=current_user)
    else:
        until = datetime.combine(form.until.data, time(23, 59)) if form.until.data else None
        billing.set_premium(org, until, admin=current_user)
    db.session.commit()
    flash(t("admin.saved"), "success")
    return _back(url_for("admin.content", kind="profil"))


@bp.post("/<kind>/<int:item_id>/loeschen")
def delete(kind, item_id):
    item = get_item(kind, item_id)
    if not SimpleForm().validate_on_submit():
        abort(400)
    images = [item.logo, item.cover_image] if isinstance(item, Organization) else [item.image]
    if isinstance(item, Organization):
        images += [e.image for e in item.events] + [o.image for o in item.offers]
    ModerationLog.record(current_user, item, ModerationAction.DELETE)
    db.session.delete(item)
    db.session.commit()
    editing.delete_files(images)
    flash(t("admin.deleted"), "success")
    return redirect(url_for("admin.content", kind=kind))


# ---- edit any content ------------------------------------------------------------

@bp.route("/<kind>/<int:item_id>/bearbeiten", methods=["GET", "POST"])
def edit(kind, item_id):
    item = get_item(kind, item_id)
    form, template, load, ctx = {
        "veranstaltung": (EventForm, "dashboard/event_form.html", editing.load_event, "event"),
        "angebot": (OfferForm, "dashboard/offer_form.html", editing.load_offer, "offer"),
        "profil": (OrganizationForm, "dashboard/org_form.html", editing.load_organization, "org"),
    }[kind]
    form = form()
    if isinstance(item, Event):
        form.category_id.choices = editing.category_choices()
        form.original_start = item.start_at
    if not form.is_submitted():
        load(form, item)
    render = lambda: render_template(template, form=form, admin_mode=True,  # noqa: E731
                                     back_url=url_for("admin.content", kind=kind), **{ctx: item})

    if form.validate_on_submit():
        try:
            if isinstance(item, Event):
                old_files = editing.fill_event(item, form, item.organization)
            elif isinstance(item, Offer):
                old_files = editing.fill_offer(item, form)
            else:
                old_files = editing.fill_organization(item, form)
        except ImageError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render()
        # Admin edits keep the current status: no re-review of your own changes.
        ModerationLog.record(current_user, item, ModerationAction.EDIT)
        db.session.commit()
        editing.delete_files(old_files)
        flash(t("admin.saved"), "success")
        return redirect(url_for("admin.content", kind=kind))
    return render()


# ---- content lists ------------------------------------------------------------------

@bp.get("/inhalte/<kind>")
def content(kind):
    model = KINDS.get(kind) or abort(404)
    status = request.args.get("status", "")
    q = " ".join(request.args.get("q", "").split())[:100]
    stmt = select(model)
    if status in Status.ALL:
        stmt = stmt.where(model.status == status)
    if q:
        text_col = model.name if model is Organization else model.title
        stmt = stmt.where(text_col.icontains(q, autoescape=True))
    order = {Event: Event.start_at.desc(), Offer: Offer.valid_from.desc(), Organization: Organization.name}[model]
    page = db.paginate(stmt.order_by(order), page=request.args.get("seite", 1, type=int),
                       per_page=PER_PAGE, error_out=False)
    return render_template("admin/content.html", kind=kind, page=page, status=status, q=q,
                           premium_form=PremiumForm(), now=now_local())


# ---- users ------------------------------------------------------------------------

@bp.get("/nutzer")
def users():
    q = " ".join(request.args.get("q", "").split())[:100]
    stmt = select(User)
    if q:
        stmt = stmt.where(User.email.icontains(q, autoescape=True))
    page = db.paginate(stmt.order_by(User.created_at.desc()), page=request.args.get("seite", 1, type=int),
                       per_page=PER_PAGE, error_out=False)
    return render_template("admin/users.html", page=page, q=q)


@bp.post("/nutzer/<int:user_id>/sperren")
def toggle_block(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.id == current_user.id or not SimpleForm().validate_on_submit():
        abort(400)
    user.is_blocked = not user.is_blocked
    if user.is_blocked:
        ApiToken.revoke_all(user.id)  # also log out of the app
    ModerationLog.record(current_user, user, ModerationAction.BLOCK if user.is_blocked else ModerationAction.UNBLOCK)
    db.session.commit()
    flash(t("admin.saved"), "success")
    return _back(url_for("admin.users"))


@bp.post("/nutzer/<int:user_id>/loeschen")
def delete_user(user_id):
    from ..dashboard.routes import erase_user

    user = db.session.get(User, user_id) or abort(404)
    if user.id == current_user.id or not SimpleForm().validate_on_submit():
        abort(400)
    ModerationLog.record(current_user, user, ModerationAction.DELETE)
    erase_user(user)  # commits; also anonymizes the log entry above
    flash(t("admin.deleted"), "success")
    return redirect(url_for("admin.users"))


# ---- categories --------------------------------------------------------------------

@bp.get("/kategorien")
def categories():
    rows = db.session.execute(
        select(Category, func.count(Event.id)).outerjoin(Event).group_by(Category.id)
        .order_by(Category.sort_order)).all()
    return render_template("admin/categories.html", rows=rows)


@bp.route("/kategorien/neu", methods=["GET", "POST"], defaults={"cat_id": None})
@bp.route("/kategorien/<int:cat_id>", methods=["GET", "POST"])
def category_edit(cat_id):
    cat = (db.session.get(Category, cat_id) or abort(404)) if cat_id else None
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        duplicate = db.session.scalar(select(Category).where(Category.name == form.name.data,
                                                             Category.id != (cat.id if cat else 0)))
        if duplicate:
            form.name.errors.append(t("admin.category_exists"))
        else:
            cat = cat or Category()
            form.populate_obj(cat)  # slug is set once on create and then stays stable for URLs
            cat.sort_order = cat.sort_order or 0
            db.session.add(cat)
            db.session.commit()
            flash(t("admin.saved"), "success")
            return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, cat=cat)


@bp.post("/kategorien/<int:cat_id>/loeschen")
def category_delete(cat_id):
    cat = db.session.get(Category, cat_id) or abort(404)
    if SimpleForm().validate_on_submit():
        db.session.delete(cat)  # events keep existing, without category (ON DELETE SET NULL)
        db.session.commit()
        flash(t("admin.deleted"), "success")
    return redirect(url_for("admin.categories"))


# ---- moderation log -------------------------------------------------------------------

@bp.get("/protokoll")
def log():
    page = db.paginate(select(ModerationLog).order_by(ModerationLog.created_at.desc()),
                       page=request.args.get("seite", 1, type=int), per_page=50, error_out=False)
    return render_template("admin/log.html", page=page)
