"""Custom error pages."""
from flask import current_app, render_template, request

from .extensions import db
from .i18n import t


def register_error_handlers(app) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return render_template("errors/generic.html", code=413, title=t("errors.413_title"),
                               text=t("errors.413_text", mb=mb), back=request.referrer), 413

    @app.errorhandler(429)
    def too_many(_error):
        return render_template("errors/generic.html", code=429, title=t("errors.429_title"),
                               text=t("errors.429_text"), back=request.referrer), 429

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()  # a failed transaction must not poison the next request
        app.logger.exception("Unhandled error: %s", error)
        return render_template("errors/500.html"), 500
