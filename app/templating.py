"""Jinja filters and globals: German date formatting, prices, safe HTML."""
import hashlib
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from flask import current_app, g, request, url_for
from markupsafe import Markup
from sqlalchemy import select

from .extensions import db
from .i18n import t
from .utils.html import sanitize_html, to_plain_text
from .utils.timeutils import now_local


def date_short(value: date | datetime) -> str:
    """'Sa, 14. Nov.'"""
    return f"{t('dates.weekdays_short')[value.weekday()]}, {value.day}. {t('dates.months_short')[value.month - 1]}"


def date_long(value: date | datetime) -> str:
    """'Samstag, 14. November 2026'"""
    return (f"{t('dates.weekdays')[value.weekday()]}, {value.day}. "
            f"{t('dates.months')[value.month - 1]} {value.year}")


def date_numeric(value: date | datetime) -> str:
    return f"{value:%d.%m.%Y}"


def day_label(value: date | datetime, today: date | None = None) -> str:
    """'Heute', 'Morgen' or 'Sa, 14. Nov.'"""
    today = today or now_local().date()
    day = value.date() if isinstance(value, datetime) else value
    if day == today:
        return t("dates.today")
    if day == today + timedelta(days=1):
        return t("dates.tomorrow")
    return date_short(day)


def format_when(start: datetime, end: datetime | None = None) -> str:
    """Human-readable time span: 'Heute, 19:30–22:00 Uhr' or '26. Nov. – 23. Dez.'"""
    if end and end.date() != start.date() and end - start > timedelta(hours=12):
        months = t("dates.months_short")
        return f"{start.day}. {months[start.month - 1]} – {end.day}. {months[end.month - 1]}"
    times = f"{start:%H:%M}" + (f"–{end:%H:%M}" if end else "")
    return f"{day_label(start)}, {t('dates.time', time=times)}"


def format_price(event) -> str:
    if event.is_free:
        return t("events.free")
    return event.price_info or t("events.price_paid")


def rich_html(value: str | None) -> Markup:
    return Markup(sanitize_html(value))


def url_with(**changes) -> str:
    """Current URL with some query parameters replaced (None removes one)."""
    args = request.args.to_dict()
    args.update(changes)
    args = {k: v for k, v in args.items() if v not in (None, "")}
    return url_for(request.endpoint, **(request.view_args or {}), **args)


@lru_cache(maxsize=128)
def _file_hash(path: str, mtime: float) -> str:
    return hashlib.md5(Path(path).read_bytes(), usedforsecurity=False).hexdigest()[:10]


def asset(filename: str) -> str:
    """Static URL with a content hash (?v=…): browsers may cache it for a year,
    and every change to the file produces a new URL automatically."""
    path = Path(current_app.static_folder) / filename
    try:
        version = _file_hash(str(path), path.stat().st_mtime)
    except OSError:
        version = "0"
    return url_for("static", filename=filename, v=version)


def asset_version() -> str:
    """One hash over the core files; changes whenever CSS/JS change (service worker cache name)."""
    files = ["css/app.css", "js/app.js", "js/map.js", "js/theme-init.js"]
    return hashlib.md5("".join(asset(f) for f in files).encode(), usedforsecurity=False).hexdigest()[:10]


def upload_url(filename: str | None, small: bool = False) -> str | None:
    if not filename:
        return None
    from .services.images import small_variant

    return url_for("public.uploaded_file", filename=small_variant(filename) if small else filename)


def nav_categories():
    if "nav_categories" not in g:
        from .models import Category

        g.nav_categories = db.session.scalars(select(Category).order_by(Category.sort_order)).all()
    return g.nav_categories


def register_templating(app) -> None:
    app.jinja_env.filters.update(
        date_short=date_short, date_long=date_long, date_numeric=date_numeric,
        day_label=day_label, when=format_when, price=format_price,
        rich=rich_html, plain=to_plain_text,
    )
    from .services import seo

    app.jinja_env.globals.update(t=t, url_with=url_with, nav_categories=nav_categories,
                                 upload_url=upload_url, asset=asset, seo=seo)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    @app.context_processor
    def _site_context():
        return {
            "site_name": app.config["SITE_NAME"],
            "site_url": app.config["SITE_URL"],
            "now": now_local(),
        }
