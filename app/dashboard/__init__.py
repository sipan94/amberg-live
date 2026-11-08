from flask import Blueprint

bp = Blueprint("dashboard", __name__, url_prefix="/konto")

from . import routes  # noqa: E402,F401
