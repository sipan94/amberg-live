"""Time helpers.

Convention used across the app:
- created_at / updated_at and other bookkeeping columns: naive UTC.
- Event and offer times: naive *local* Amberg time (Europe/Berlin). An event at
  "every Friday 19:00" stays at 19:00 across daylight-saving changes.
"""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from flask import current_app, has_app_context

DEFAULT_TZ = "Europe/Berlin"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_tz() -> ZoneInfo:
    name = current_app.config.get("TIMEZONE", DEFAULT_TZ) if has_app_context() else DEFAULT_TZ
    return ZoneInfo(name)


def now_local() -> datetime:
    return datetime.now(local_tz()).replace(tzinfo=None, microsecond=0)


def today_local() -> date:
    return now_local().date()
