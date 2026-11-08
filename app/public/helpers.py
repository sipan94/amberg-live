"""Shared helpers for public views: query-string parsing and visibility checks."""
import re
from datetime import date, timedelta

from flask import abort, request
from flask_login import current_user
from sqlalchemy import update

from ..extensions import db
from ..services.events import EventFilter, day_start, today_window, weekend_window
from ..services.stats import is_bot, track

PERIODS = ("heute", "wochenende", "woche", "monat", "alle")
PRICES = ("kostenlos", "kostenpflichtig")
_SLUG_RE = re.compile(r"^[a-z0-9-]{1,100}$")
MAX_RANGE = timedelta(days=366)


def parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def parse_event_filter(args, now) -> tuple[EventFilter, dict]:
    """Turn ?zeitraum=…&von=…&bis=…&kategorie=…&preis=…&q=… into an EventFilter.

    Lists never show the past, so every window starts at `now` at the earliest.
    Invalid values are ignored instead of raising errors.
    """
    period = args.get("zeitraum", "")
    von, bis = parse_date(args.get("von")), parse_date(args.get("bis"))
    if von and bis and bis < von:
        von, bis = bis, von

    if von or bis:
        period = "eigener"
        start = max(now, day_start(von)) if von else now
        end = day_start(bis + timedelta(days=1)) if bis else start + timedelta(days=30)
    elif period == "heute":
        start, end = today_window(now)
    elif period == "wochenende":
        start, end = weekend_window(now)
    elif period == "woche":
        start, end = now, now + timedelta(days=7)
    elif period == "monat":
        start, end = now, now + timedelta(days=30)
    else:
        period = "alle"
        start, end = now, now + MAX_RANGE
    end = min(max(end, start), start + MAX_RANGE)

    category = args.get("kategorie", "")
    price = args.get("preis", "")
    q = " ".join(args.get("q", "").split())[:100]

    f = EventFilter(
        start=start, end=end,
        category=category if _SLUG_RE.match(category) else None,
        price=price if price in PRICES else None,
        q=q or None,
    )
    state = {"period": period, "von": von, "bis": bis, "category": f.category,
             "price": f.price, "q": q, "active": bool(f.category or f.price or q or von or bis
                                                        or period not in ("alle", ""))}
    return f, state


def can_preview(item) -> bool:
    """Owners and admins may see their own pending or rejected items."""
    if not current_user.is_authenticated:
        return False
    return current_user.is_admin or item.organization.owner_id == current_user.id


def get_visible_or_404(item):
    if item is None or not (item.is_public or can_preview(item)):
        abort(404)
    return item


def count_view(model, item) -> None:
    """Atomic +1 on view_count (no race between parallel requests) plus the daily counter.
    Skips bots and owner/admin previews."""
    if is_bot() or not item.is_public:
        return
    db.session.execute(update(model).where(model.id == item.id)
                       .values(view_count=model.view_count + 1))
    track(f"{model.__tablename__.rstrip('s')}:{item.id}", commit=False)
    db.session.commit()
