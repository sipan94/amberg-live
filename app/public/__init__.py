from flask import Blueprint

bp = Blueprint("public", __name__)

from . import events, offers, organizations, routes, seo  # noqa: E402,F401
