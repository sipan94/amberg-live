"""Privacy-friendly statistics: anonymous daily counters. No IP, no cookie, no user ID stored."""
from datetime import timedelta

from flask import request
from sqlalchemy import func, select

from ..extensions import db
from ..models import DailyStat
from ..utils.timeutils import today_local

BOT_MARKERS = ("bot", "spider", "crawl", "slurp", "preview", "monitor", "curl", "python-requests")


def is_bot() -> bool:
    agent = (request.user_agent.string or "").lower()
    return not agent or any(marker in agent for marker in BOT_MARKERS)


def track(key: str, commit: bool = True) -> None:
    """Count one view for `key` today (e.g. "page:home", "event:12"). Bots are ignored."""
    if is_bot():
        return
    DailyStat.bump(key, today_local())
    if commit:
        db.session.commit()


def daily_totals(days: int = 30) -> list[tuple]:
    """[(date, views)] for the last `days` days, including days with zero views."""
    start = today_local() - timedelta(days=days - 1)
    rows = dict(db.session.execute(
        select(DailyStat.day, func.sum(DailyStat.count)).where(DailyStat.day >= start)
        .group_by(DailyStat.day)).all())
    return [(start + timedelta(days=i), int(rows.get(start + timedelta(days=i), 0))) for i in range(days)]
