"""Custom error pages – HTML for the website, JSON for the app API (/api/...)."""
from flask import current_app, jsonify, render_template, request

from .extensions import db
from .i18n import t


def _wants_json() -> bool:
    return request.path.startswith("/api/")


def register_error_handlers(app) -> None:
    @app.errorhandler(400)
    def bad_request(error):
        if _wants_json():
            return jsonify(error=t("form.check_errors")), 400
        return error

    @app.errorhandler(404)
    def not_found(_error):
        if _wants_json():
            return jsonify(error=t("errors.404_title")), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(405)
    def not_allowed(error):
        if _wants_json():
            return jsonify(error="Method not allowed"), 405
        return error

    @app.errorhandler(413)
    def too_large(_error):
        mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        if _wants_json():
            return jsonify(error=t("validation.file_too_large", mb=mb)), 413
        return render_template("errors/generic.html", code=413, title=t("errors.413_title"),
                               text=t("errors.413_text", mb=mb), back=request.referrer), 413

    @app.errorhandler(429)
    def too_many(_error):
        if _wants_json():
            return jsonify(error=t("errors.429_text")), 429
        return render_template("errors/generic.html", code=429, title=t("errors.429_title"),
                               text=t("errors.429_text"), back=request.referrer), 429

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()  # a failed transaction must not poison the next request
        app.logger.exception("Unhandled error: %s", error)
        if _wants_json():
            return jsonify(error=t("errors.500_text")), 500
        return render_template("errors/500.html"), 500
