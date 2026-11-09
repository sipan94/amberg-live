"""JSON API for the mobile app: /api/v1/...

Authentication: `Authorization: Bearer <token>` (from POST /api/v1/auth/login).
The API never uses the browser session cookie, so it needs no CSRF protection and
cannot be abused from other websites with a visitor's logged-in session.
"""
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.datastructures import CombinedMultiDict, MultiDict

from ..extensions import csrf
from ..i18n import t
from ..models import ApiToken

bp = Blueprint("api", __name__, url_prefix="/api/v1")
csrf.exempt(bp)


@bp.before_request
def _authenticate():
    g.api_user = None
    g.api_token = None
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        token = ApiToken.find(header[7:].strip())
        if token is not None and not token.user.is_blocked:
            token.touch()
            g.api_token, g.api_user = token, token.user


# Only for the Expo web preview during development (phones don't need CORS).
DEV_PREVIEW_ORIGINS = {"http://localhost:8081", "http://127.0.0.1:8081"}


@bp.after_request
def _dev_cors(response):
    origin = request.headers.get("Origin")
    if current_app.debug and origin in DEV_PREVIEW_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        response.headers["Vary"] = "Origin"
    return response


def error(message: str, status: int = 400, **extra):
    return jsonify(error=message, **extra), status


def form_errors(form):
    """WTForms errors as {"field": ["message", ...]} – messages are German, from de.json."""
    return jsonify(error=t("form.check_errors"),
                   fields={name: [str(e) for e in errs] for name, errs in form.errors.items()}), 422


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.api_user is None:
            return error(t("auth.login_required"), 401)
        return view(*args, **kwargs)
    return wrapper


def verified_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not g.api_user.is_verified:
            return error(t("dashboard.verify_first"), 403, code="not_verified")
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not g.api_user.is_admin:
            return error(t("errors.404_title"), 404)
        return view(*args, **kwargs)
    return wrapper


def bind(form_class, obj=None, **kwargs):
    """Fill a website form (same validation, same German messages) from JSON or multipart data."""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        formdata = MultiDict({k: ("" if v is None else v) for k, v in data.items() if not isinstance(v, (list, dict))})
    else:
        formdata = CombinedMultiDict([request.files, request.form])
    return form_class(formdata=formdata, obj=obj, meta={"csrf": False}, **kwargs)


def page_meta(page) -> dict:
    return {"page": page.page, "pages": page.pages, "total": page.total,
            "has_next": page.has_next, "has_prev": page.has_prev}


from . import admin, auth, dashboard, public  # noqa: E402,F401
