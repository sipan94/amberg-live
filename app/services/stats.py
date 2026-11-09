"""Privacy-friendly statistics: anonymous daily counters. No IP, no cookie, no user ID stored."""
from datetime import timedelta

from flask import request
from sqlalchemy import func, or_, select

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


def admin_overview() -> dict:
    """Numbers for the admin start page (web) and the admin screen in the app."""
    from ..models import Event, ModerationLog, Offer, Organization, Role, Status, User
    from ..utils.timeutils import now_local, utcnow
    from .events import EventFilter, find_occurrences, first_per_event

    now = now_local()
    week_ago = utcnow() - timedelta(days=7)

    def count(stmt) -> int:
        return db.session.scalar(stmt) or 0

    stats = {
        "users": count(select(func.count(User.id)).where(User.role == Role.ORG)),
        "users_new": count(select(func.count(User.id)).where(User.created_at >= week_ago)),
        "orgs": count(select(func.count(Organization.id)).where(Organization.status == Status.APPROVED)),
        "premium": count(select(func.count(Organization.id)).where(Organization.is_premium.is_(True))),
        "events_upcoming": len(first_per_event(find_occurrences(EventFilter(now, now + timedelta(days=30))))),
        "offers": count(select(func.count(Offer.id)).where(
            Offer.status == Status.APPROVED,
            or_(Offer.valid_until.is_(None), Offer.valid_until >= now.date()))),
    }
    days = daily_totals(30)
    return {
        "stats": stats,
        "days": days,
        "views_total": sum(v for _, v in days),
        "top_events": db.session.scalars(select(Event).where(Event.status == Status.APPROVED)
                                         .order_by(Event.view_count.desc()).limit(5)).all(),
        "recent": db.session.scalars(select(ModerationLog)
                                     .order_by(ModerationLog.created_at.desc()).limit(8)).all(),
    }


def daily_totals(days: int = 30) -> list[tuple]:
    """[(date, views)] for the last `days` days, including days with zero views."""
    start = today_local() - timedelta(days=days - 1)
    rows = dict(db.session.execute(
        select(DailyStat.day, func.sum(DailyStat.count)).where(DailyStat.day >= start)
        .group_by(DailyStat.day)).all())
    return [(start + timedelta(days=i), int(rows.get(start + timedelta(days=i), 0))) for i in range(days)]
