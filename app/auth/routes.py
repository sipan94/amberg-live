"""Register, verify e-mail, log in/out, reset password."""
from urllib.parse import urlsplit

from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select

from ..extensions import db, limiter, login_manager
from ..forms.auth import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm, SimpleForm
from ..i18n import t
from ..models import ApiToken, Role, User
from ..services.mail import send_mail
from ..services.tokens import RESET_MAX_AGE, VERIFY_MAX_AGE, make_reset_token, make_verify_token, read_token
from ..utils.timeutils import utcnow
from . import bp


@login_manager.unauthorized_handler
def _unauthorized():
    flash(t("auth.login_required"), "info")
    return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))


def _safe_next(target: str | None) -> str | None:
    """Only allow redirects to our own site (prevents 'open redirect' phishing links)."""
    if not target:
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


def _home_for(user) -> str:
    return url_for("admin.index") if user.is_admin else url_for("dashboard.index")


def send_verification(user: User) -> None:
    send_mail(user.email, t("emails.verify_subject"), "verify",
              link=url_for("auth.verify", token=make_verify_token(user), _external=True))


def _find_user(email: str) -> User | None:
    return db.session.scalar(select(User).where(User.email == email.strip().lower()))


@bp.route("/registrieren", methods=["GET", "POST"])
@limiter.limit("5/hour;20/day", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    form = RegisterForm()
    if form.validate_on_submit():
        existing = _find_user(form.email.data)
        if existing:
            # Same response as a new sign-up, so nobody can test which e-mails exist.
            send_mail(existing.email, t("emails.already_subject"), "already_registered",
                      login_url=url_for("auth.login", _external=True),
                      reset_url=url_for("auth.forgot_password", _external=True))
        else:
            user = User(email=form.email.data, role=Role.ORG)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            send_verification(user)
        return redirect(url_for("auth.check_email"))
    return render_template("auth/register.html", form=form)


@bp.get("/registrieren/fast-geschafft")
def check_email():
    return render_template("auth/check_email.html")


@bp.get("/bestaetigen/<token>")
def verify(token):
    data = read_token(token, "verify", VERIFY_MAX_AGE)
    user = db.session.get(User, data["uid"]) if data else None
    if user is None or user.email != data.get("email"):
        flash(t("auth.verify_invalid"), "error")
        return redirect(url_for("auth.login"))
    if not user.is_verified:
        user.is_verified = True
        user.verified_at = utcnow()
        db.session.commit()
    flash(t("auth.verify_ok"), "success")
    return redirect(url_for("dashboard.index") if current_user.is_authenticated else url_for("auth.login"))


@bp.post("/bestaetigen/erneut")
@login_required
@limiter.limit("3/hour")
def resend_verification():
    if SimpleForm().validate_on_submit() and not current_user.is_verified:
        send_verification(current_user)
        flash(t("auth.verify_resent"), "success")
    return redirect(url_for("dashboard.index"))


@bp.route("/anmelden", methods=["GET", "POST"])
@limiter.limit("10/minute;50/hour", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = _find_user(form.email.data)
        if user is None:
            User.spend_hash_time(form.password.data)
        elif user.check_password(form.password.data):
            if user.is_blocked:
                flash(t("auth.blocked"), "error")
                return render_template("auth/login.html", form=form), 403
            session.clear()  # fresh session on login (prevents session fixation)
            login_user(user)
            user.last_login_at = utcnow()
            db.session.commit()  # also saves an upgraded password hash
            return redirect(_safe_next(request.args.get("next")) or _home_for(user))
        # Logged with IP for attack detection; logs rotate (see Datenschutzerklärung).
        current_app.logger.warning("Failed login from %s", request.remote_addr)
        flash(t("auth.login_failed"), "error")
    return render_template("auth/login.html", form=form)


@bp.post("/abmelden")
@login_required
def logout():
    if SimpleForm().validate_on_submit():
        logout_user()
        session.clear()
        flash(t("auth.logged_out"), "success")
    return redirect(url_for("public.home"))


@bp.route("/passwort-vergessen", methods=["GET", "POST"])
@limiter.limit("5/hour", methods=["POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = _find_user(form.email.data)
        if user and not user.is_blocked:
            send_mail(user.email, t("emails.reset_subject"), "reset",
                      link=url_for("auth.reset_password", token=make_reset_token(user), _external=True))
        flash(t("auth.reset_sent"), "success")  # same message whether the account exists or not
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot.html", form=form)


@bp.route("/passwort-neu/<token>", methods=["GET", "POST"])
@limiter.limit("10/hour", methods=["POST"])
def reset_password(token):
    data = read_token(token, "reset", RESET_MAX_AGE)
    user = db.session.get(User, data["uid"]) if data else None
    if user is None or user.password_hash[-12:] != data.get("ph"):
        flash(t("auth.reset_invalid"), "error")
        return redirect(url_for("auth.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        ApiToken.revoke_all(user.id)  # log out all app devices
        if not user.is_verified:  # the link proved they own the address
            user.is_verified, user.verified_at = True, utcnow()
        db.session.commit()
        flash(t("auth.reset_ok"), "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)


@bp.app_context_processor
def _auth_context():
    # A CSRF-protected form for the logout button in the header.
    return {"logout_form": SimpleForm() if current_user.is_authenticated else None}
