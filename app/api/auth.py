"""Accounts in the app: register, log in (token), log out, password, delete account.
Same rules as the website: no account enumeration, rate limits, German messages."""
from flask import current_app, g, jsonify, request, url_for
from sqlalchemy import func, select

from ..extensions import db, limiter
from ..forms.auth import (ChangePasswordForm, DeleteAccountForm, ForgotPasswordForm, LoginForm,
                          RegisterForm)
from ..i18n import t
from ..models import ApiToken, Organization, Role, User
from ..services.mail import send_mail
from ..services.tokens import make_reset_token
from ..utils.timeutils import utcnow
from . import bind, bp, error, form_errors, login_required
from . import serializers as ser


def _find_user(email: str) -> User | None:
    return db.session.scalar(select(User).where(User.email == (email or "").strip().lower()))


def _own_org(user) -> Organization | None:
    return db.session.scalar(select(Organization).where(Organization.owner_id == user.id).order_by(Organization.id))


@bp.post("/auth/register")
@limiter.limit("5/hour;20/day")
def api_register():
    from ..auth.routes import send_verification

    form = bind(RegisterForm)
    if not form.validate():
        return form_errors(form)
    existing = _find_user(form.email.data)
    if existing:
        # Identical answer for new and existing addresses (no account enumeration).
        send_mail(existing.email, t("emails.already_subject"), "already_registered",
                  login_url=url_for("auth.login", _external=True),
                  reset_url=url_for("auth.forgot_password", _external=True))
    else:
        user = User(email=form.email.data, role=Role.ORG)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        send_verification(user)
    return jsonify(message=t("auth.check_email_text")), 201


@bp.post("/auth/login")
@limiter.limit("10/minute;50/hour")
def api_login():
    form = bind(LoginForm)
    if not form.validate():
        return form_errors(form)
    user = _find_user(form.email.data)
    if user is None:
        User.spend_hash_time(form.password.data)
    elif user.check_password(form.password.data):
        if user.is_blocked:
            return error(t("auth.blocked"), 403, code="blocked")
        device = (request.get_json(silent=True) or {}).get("device") if request.is_json else request.form.get("device")
        plain, _token = ApiToken.issue(user, device)
        user.last_login_at = utcnow()
        db.session.commit()
        return jsonify(token=plain, user=ser.user(user, _own_org(user)))
    current_app.logger.warning("Failed app login from %s", request.remote_addr)
    return error(t("auth.login_failed"), 401)


@bp.post("/auth/logout")
@login_required
def api_logout():
    db.session.delete(g.api_token)
    db.session.commit()
    return jsonify(message=t("auth.logged_out"))


@bp.get("/auth/me")
@login_required
def api_me():
    from ..models import Event, Offer, Status

    data = ser.user(g.api_user, _own_org(g.api_user))
    if g.api_user.is_admin:
        data["pending"] = sum(db.session.scalar(select(func.count(m.id)).where(m.status == Status.PENDING)) or 0
                              for m in (Event, Offer, Organization))
    return jsonify(data)


@bp.post("/auth/resend-verification")
@login_required
@limiter.limit("3/hour")
def api_resend_verification():
    from ..auth.routes import send_verification

    if not g.api_user.is_verified:
        send_verification(g.api_user)
    return jsonify(message=t("auth.verify_resent"))


@bp.post("/auth/forgot-password")
@limiter.limit("5/hour")
def api_forgot_password():
    form = bind(ForgotPasswordForm)
    if not form.validate():
        return form_errors(form)
    user = _find_user(form.email.data)
    if user and not user.is_blocked:
        # The link opens the website, where the new password is set.
        send_mail(user.email, t("emails.reset_subject"), "reset",
                  link=url_for("auth.reset_password", token=make_reset_token(user), _external=True))
    return jsonify(message=t("auth.reset_sent"))


@bp.post("/auth/change-password")
@login_required
@limiter.limit("10/hour")
def api_change_password():
    form = bind(ChangePasswordForm)
    if not form.validate():
        return form_errors(form)
    if not g.api_user.check_password(form.current_password.data):
        return error(t("validation.wrong_password"), 422,
                     fields={"current_password": [t("validation.wrong_password")]})
    g.api_user.set_password(form.password.data)
    ApiToken.revoke_all(g.api_user.id, except_id=g.api_token.id)  # log out other devices
    db.session.commit()
    return jsonify(message=t("dashboard.password_changed"))


@bp.post("/auth/delete-account")
@login_required
@limiter.limit("10/hour")
def api_delete_account():
    """DSGVO: delete account with all content and images, from the app."""
    from ..dashboard.routes import erase_user

    form = bind(DeleteAccountForm)
    if not form.validate():
        return form_errors(form)
    user = g.api_user
    if not user.check_password(form.password.data):
        return error(t("validation.wrong_password"), 422, fields={"password": [t("validation.wrong_password")]})
    if user.is_admin and db.session.scalar(select(func.count(User.id)).where(User.role == Role.ADMIN)) <= 1:
        return error(t("dashboard.last_admin"), 409)
    erase_user(user)
    return jsonify(message=t("dashboard.account_deleted"))
