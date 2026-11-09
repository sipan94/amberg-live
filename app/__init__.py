"""Amberg Live - application factory."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import get_config
from .extensions import csrf, db, limiter, login_manager, migrate


def create_app(config_name: str | None = None, overrides: dict | None = None) -> Flask:
    """`overrides` lets tests change settings before extensions read them (e.g. rate limits)."""
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    config_class = get_config(config_name)
    app.config.from_object(config_class)
    app.config.update(overrides or {})
    config_class.init_app(app)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    proxies = app.config["PROXY_COUNT"]
    if proxies:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=proxies)

    _configure_logging(app)
    _init_extensions(app)
    _register_blueprints(app)

    from .errors import register_error_handlers
    from .security import register_security
    from .templating import register_templating

    register_templating(app)
    register_error_handlers(app)
    register_security(app)

    from .cli import register_cli

    register_cli(app)
    app.logger.info("Amberg Live started with %s", config_class.__name__)
    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    is_sqlite = app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")
    # SQLite can't ALTER most things; batch mode makes Alembic copy tables instead.
    migrate.init_app(app, db, render_as_batch=is_sqlite)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    limiter.exempt(app.view_functions["static"])  # CSS/JS/icons never count against the limit

    from . import models  # noqa: F401  (registers models with SQLAlchemy)
    from .utils.slugs import register_slug_listener

    register_slug_listener()


def _register_blueprints(app: Flask) -> None:
    from .admin import bp as admin_bp
    from .api import bp as api_bp
    from .auth import bp as auth_bp
    from .dashboard import bp as dashboard_bp
    from .public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, str(app.config["LOG_LEVEL"]).upper(), logging.INFO)
    app.logger.setLevel(level)
    if app.debug or app.testing:
        return
    log_dir = Path(app.config["LOG_DIR"])
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "amberg_live.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    handler.setLevel(level)
    app.logger.addHandler(handler)
