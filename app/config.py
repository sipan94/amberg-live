"""Configuration classes. All secrets and environment-specific values come from .env."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{(BASE_DIR / 'instance' / 'amberg_live.db').as_posix()}"
    # Some hosts hand out "postgres://" URLs; SQLAlchemy needs an explicit driver.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    ENV_NAME = "base"

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SITE_NAME = "Amberg Live"
    SITE_URL = os.environ.get("SITE_URL", "http://localhost:5000").rstrip("/")
    TIMEZONE = "Europe/Berlin"
    DEFAULT_LOCALE = "de"
    PER_PAGE = 12

    # Uploads live outside the code folder so deployments never overwrite them.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "instance" / "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "8")) * 1024 * 1024

    # Only one cookie: the technically necessary session cookie (no "remember me" cookie).
    SESSION_COOKIE_NAME = "al_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 14  # 14 days

    WTF_CSRF_TIME_LIMIT = None  # token lives as long as the session

    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    # Generous site-wide limit against scrapers; stricter limits sit on login/register/submit.
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "300 per minute")

    # Reject requests with a foreign Host header (e.g. "amberg-live.de,www.amberg-live.de").
    TRUSTED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()] or None

    # Outgoing mail (email verification, password reset). Empty host = print mails to log.
    MAIL_HOST = os.environ.get("MAIL_HOST", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", True)
    MAIL_FROM = os.environ.get("MAIL_FROM", "Amberg Live <noreply@example.com>")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")

    # Address -> coordinates when businesses save an address. The request is made by the
    # server (not the visitor's browser), so no visitor data reaches OpenStreetMap.
    GEOCODER_ENABLED = _env_bool("GEOCODER_ENABLED", True)
    NOMINATIM_URL = os.environ.get("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")

    # Number of reverse proxies (nginx = 1) in front of the app, for correct client IPs.
    PROXY_COUNT = int(os.environ.get("PROXY_COUNT", "0"))

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_DIR = os.environ.get("LOG_DIR", str(BASE_DIR / "instance" / "logs"))

    @classmethod
    def init_app(cls, app) -> None:
        pass


class DevelopmentConfig(Config):
    ENV_NAME = "development"
    DEBUG = True
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")


class TestingConfig(Config):
    ENV_NAME = "testing"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    GEOCODER_ENABLED = False
    MAIL_HOST = ""
    SECRET_KEY = "testing-secret"
    SERVER_NAME = "localhost"


class ProductionConfig(Config):
    ENV_NAME = "production"
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"
    # Static URLs carry a content hash (?v=…), so browsers may keep them for a year.
    SEND_FILE_MAX_AGE_DEFAULT = 60 * 60 * 24 * 365
    PROXY_COUNT = int(os.environ.get("PROXY_COUNT", "1"))

    @classmethod
    def init_app(cls, app) -> None:
        key = app.config.get("SECRET_KEY", "")
        if not key or key.startswith("dev-") or len(key) < 32:
            raise RuntimeError("Set a strong SECRET_KEY (32+ chars) in .env for production.")


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    name = name or os.environ.get("APP_ENV", "development")
    try:
        return _CONFIGS[name]
    except KeyError:
        raise RuntimeError(f"Unknown APP_ENV '{name}'. Use one of: {', '.join(_CONFIGS)}") from None
