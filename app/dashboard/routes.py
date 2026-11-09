"""Business/club dashboard: profile, events, offers, account settings."""
from functools import wraps

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func, select, update

from ..extensions import db, limiter
from ..forms.auth import ChangePasswordForm, DeleteAccountForm, SimpleForm
from ..forms.dashboard import EventForm, OfferForm, OrganizationForm
from ..i18n import t
from ..models import ApiToken, Event, ModerationLog, Offer, Organization, Role, User
from ..services import editing, moderation
from ..services.images import ImageError, delete_image
from ..utils.timeutils import now_local
from . import bp

SUBMIT_LIMIT = "30/hour"


# ---- helpers ----------------------------------------------------------------

@bp.before_request
@login_required
def _require_login():
    """Every page under /konto needs a logged-in user."""


def verified_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_verified:
            flash(t("dashboard.verify_first"), "info")
            return redirect(url_for("dashboard.index"))
        return view(*args, **kwargs)
    return wrapper


def current_org() -> Organization | None:
    return db.session.scalar(
        select(Organization).where(Organization.owner_id == current_user.id).order_by(Organization.id))


def org_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_org() is None:
            flash(t("dashboard.profile_first"), "info")
            return redirect(url_for("dashboard.profile"))
        return view(*args, **kwargs)
    return wrapper


def get_own(model, item_id: int):
    """Load an event/offer of the current user, or 404 (never reveal other users' items)."""
    item = db.session.get(model, item_id)
    if item is None or item.organization.owner_id != current_user.id:
        abort(404)
    return item


def finish_submission(item, *, is_new: bool, changed: set[str], old_files):
    db.session.add(item)
    pending = moderation.submit(item, is_new=is_new, changed=changed)
    db.session.commit()
    editing.delete_files(old_files)  # only after the commit worked
    flash(t("dashboard.saved_pending") if pending else t("dashboard.saved_live"), "success")
    return redirect(url_for("dashboard.index"))


# ---- overview ---------------------------------------------------------------

@bp.get("/")
def index():
    org = current_org()
    events = offers = []
    if org:
        events = db.session.scalars(select(Event).where(Event.organization_id == org.id)
                                    .order_by(Event.start_at.desc())).all()
        offers = db.session.scalars(select(Offer).where(Offer.organization_id == org.id)
                                    .order_by(Offer.valid_from.desc())).all()
    return render_template("dashboard/index.html", org=org, events=events, offers=offers,
                           now=now_local(), form=SimpleForm())


# ---- organization profile ---------------------------------------------------

@bp.route("/profil", methods=["GET", "POST"])
@verified_required
@limiter.limit(SUBMIT_LIMIT, methods=["POST"])
def profile():
    org = current_org()
    is_new = org is None
    form = OrganizationForm()
    if not form.is_submitted() and org:
        editing.load_organization(form, org)

    if form.validate_on_submit():
        org = org or Organization(owner=current_user)
        try:
            old_files = editing.fill_organization(org, form)
        except ImageError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("dashboard/org_form.html", form=form, org=None if is_new else org)
        changed = set() if is_new else moderation.changed_fields(org)
        return finish_submission(org, is_new=is_new, changed=changed, old_files=old_files)

    return render_template("dashboard/org_form.html", form=form, org=org)


# ---- events -----------------------------------------------------------------

def _save_event(event: Event | None):
    is_new = event is None
    form = EventForm()
    form.category_id.choices = editing.category_choices()
    if event is not None:
        form.original_start = event.start_at
    if not form.is_submitted():
        if event is not None:
            editing.load_event(form, event)
        else:
            org = current_org()
            form.location_name.data, form.address.data = org.name, org.address

    if form.validate_on_submit():
        org = current_org()
        event = event or Event(organization=org)
        try:
            old_files = editing.fill_event(event, form, org)
        except ImageError as exc:
            db.session.rollback()
            form.image.errors = [str(exc)]
            return render_template("dashboard/event_form.html", form=form, event=None if is_new else event)
        changed = set() if is_new else moderation.changed_fields(event)
        return finish_submission(event, is_new=is_new, changed=changed, old_files=old_files)
    return render_template("dashboard/event_form.html", form=form, event=event)


@bp.route("/veranstaltungen/neu", methods=["GET", "POST"])
@verified_required
@org_required
@limiter.limit(SUBMIT_LIMIT, methods=["POST"])
def event_new():
    return _save_event(None)


@bp.route("/veranstaltungen/<int:event_id>", methods=["GET", "POST"])
@verified_required
@limiter.limit(SUBMIT_LIMIT, methods=["POST"])
def event_edit(event_id):
    return _save_event(get_own(Event, event_id))


@bp.post("/veranstaltungen/<int:event_id>/loeschen")
def event_delete(event_id):
    return _delete(get_own(Event, event_id))


# ---- offers -----------------------------------------------------------------

def _save_offer(offer: Offer | None):
    is_new = offer is None
    form = OfferForm()
    if not form.is_submitted() and offer is not None:
        editing.load_offer(form, offer)
    if form.validate_on_submit():
        offer = offer or Offer(organization=current_org())
        try:
            old_files = editing.fill_offer(offer, form)
        except ImageError as exc:
            db.session.rollback()
            form.image.errors = [str(exc)]
            return render_template("dashboard/offer_form.html", form=form, offer=None if is_new else offer)
        changed = set() if is_new else moderation.changed_fields(offer)
        return finish_submission(offer, is_new=is_new, changed=changed, old_files=old_files)
    return render_template("dashboard/offer_form.html", form=form, offer=offer)


@bp.route("/angebote/neu", methods=["GET", "POST"])
@verified_required
@org_required
@limiter.limit(SUBMIT_LIMIT, methods=["POST"])
def offer_new():
    return _save_offer(None)


@bp.route("/angebote/<int:offer_id>", methods=["GET", "POST"])
@verified_required
@limiter.limit(SUBMIT_LIMIT, methods=["POST"])
def offer_edit(offer_id):
    return _save_offer(get_own(Offer, offer_id))


@bp.post("/angebote/<int:offer_id>/loeschen")
def offer_delete(offer_id):
    return _delete(get_own(Offer, offer_id))


def _delete(item):
    if SimpleForm().validate_on_submit():
        image = item.image
        db.session.delete(item)
        db.session.commit()
        delete_image(image)
        flash(t("dashboard.deleted"), "success")
    return redirect(url_for("dashboard.index"))


# ---- account settings -------------------------------------------------------

@bp.route("/einstellungen", methods=["GET", "POST"])
@limiter.limit("10/hour", methods=["POST"])
def settings():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            form.current_password.errors = [t("validation.wrong_password")]
        else:
            current_user.set_password(form.password.data)
            ApiToken.revoke_all(current_user.id)  # log out all app devices
            db.session.commit()
            flash(t("dashboard.password_changed"), "success")
            return redirect(url_for("dashboard.settings"))
    return render_template("dashboard/settings.html", form=form)


def user_image_paths(user: User) -> list[str | None]:
    return [p for org in user.organizations for p in
            [org.logo, org.cover_image, *(e.image for e in org.events), *(o.image for o in org.offers)]]


def erase_user(user: User) -> None:
    """Delete a user with all content (DB cascade) and image files. Used by admin too."""
    images = user_image_paths(user)
    # Moderation history stays (accountability) but no longer names the person.
    db.session.execute(update(ModerationLog)
                       .where(ModerationLog.target_type == "user", ModerationLog.target_id == user.id)
                       .values(target_label=t("dashboard.deleted_account")))
    db.session.delete(user)
    db.session.commit()
    editing.delete_files(images)


@bp.route("/loeschen", methods=["GET", "POST"])
@limiter.limit("10/hour", methods=["POST"])
def delete_account():
    """DSGVO: users delete their account and all their content themselves."""
    form = DeleteAccountForm()
    if form.validate_on_submit():
        user = db.session.get(User, current_user.id)
        if not user.check_password(form.password.data):
            form.password.errors = [t("validation.wrong_password")]
        elif user.is_admin and db.session.scalar(
                select(func.count(User.id)).where(User.role == Role.ADMIN)) <= 1:
            flash(t("dashboard.last_admin"), "error")
        else:
            logout_user()
            erase_user(user)
            flash(t("dashboard.account_deleted"), "success")
            return redirect(url_for("public.home"))
    return render_template("dashboard/delete_account.html", form=form)
