"""Event list, calendar, map, detail page and .ics download."""
import calendar as pycal
import json
from datetime import date, timedelta
from itertools import groupby
from urllib.parse import urlparse

from flask import Response, render_template, request, url_for
from sqlalchemy import select

from ..extensions import db
from ..models import Category, Event
from ..services.events import (EventFilter, day_start, find_occurrences, first_per_event,
                               last_occurrence_end, upcoming_dates)
from ..services.ics import event_to_ics
from ..services.pagination import ListPagination
from ..services.stats import track
from ..templating import format_when
from ..utils.timeutils import now_local
from . import bp
from .helpers import count_view, get_visible_or_404, parse_event_filter

PER_PAGE = 20


def _categories():
    return db.session.scalars(select(Category).order_by(Category.sort_order)).all()


@bp.get("/veranstaltungen")
def events():
    now = now_local()
    f, state = parse_event_filter(request.args, now)
    occurrences = find_occurrences(f)
    page = ListPagination(occurrences, request.args.get("seite", 1, type=int), PER_PAGE)

    # Paid placement: up to 3 highlighted events on top of the first page.
    tips = first_per_event([o for o in occurrences if o.is_highlight])[:3] if page.page == 1 else []
    days = [(day, list(items)) for day, items in groupby(page.items, key=lambda o: o.start.date())]
    track("page:events")

    return render_template("public/events_list.html", page=page, days=days, tips=tips,
                           state=state, categories=_categories(), view="list")


@bp.get("/veranstaltungen/kalender")
def events_calendar():
    now = now_local()
    try:
        year, month = map(int, request.args.get("monat", "").split("-"))
        first = date(year, month, 1)
    except ValueError:
        first = now.date().replace(day=1)
    _, f_state = parse_event_filter(request.args, now)

    days_in_month = pycal.monthrange(first.year, first.month)[1]
    grid_start = first - timedelta(days=first.weekday())
    last = first.replace(day=days_in_month)
    grid_end = last + timedelta(days=6 - last.weekday())

    f = EventFilter(start=max(day_start(grid_start), now.replace(hour=0, minute=0, second=0)),
                    end=day_start(grid_end + timedelta(days=1)),
                    category=f_state["category"], price=f_state["price"], q=f_state["q"] or None)
    by_day: dict[date, list] = {}
    for occ in find_occurrences(f) if f.start < f.end else []:
        # Multi-day events (e.g. Christkindlmarkt) appear on every day they run.
        last_day = (occ.end - timedelta(seconds=1)).date() if occ.end and occ.end > occ.start else occ.start.date()
        day = max(occ.start.date(), grid_start)
        while day <= min(last_day, grid_end):
            by_day.setdefault(day, []).append(occ)
            day += timedelta(days=1)

    weeks = []
    day = grid_start
    while day <= grid_end:
        weeks.append([(day + timedelta(days=i)) for i in range(7)])
        day += timedelta(days=7)

    prev_month = (first - timedelta(days=1)).replace(day=1)
    next_month = last + timedelta(days=1)
    return render_template("public/events_calendar.html", weeks=weeks, by_day=by_day,
                           month=first, prev_month=prev_month, next_month=next_month,
                           state=f_state, categories=_categories(), view="calendar")


@bp.get("/veranstaltungen/karte")
def events_map():
    now = now_local()
    f, state = parse_event_filter(request.args, now)
    occurrences = first_per_event(find_occurrences(f))
    markers, missing = [], 0
    for occ in occurrences:
        ev = occ.event
        if ev.lat is None or ev.lng is None:
            missing += 1
            continue
        markers.append({
            "lat": ev.lat, "lng": ev.lng, "title": ev.title,
            "url": url_for("public.event_detail", slug=ev.slug),
            "when": format_when(occ.start, occ.end),
            "place": ev.location_name or "",
            "color": ev.category.color if ev.category else "#64748b",
        })
    return render_template("public/events_map.html", markers_json=json.dumps(markers),
                           count=len(markers), missing=missing, state=state,
                           categories=_categories(), view="map")


@bp.get("/veranstaltungen/<slug>")
def event_detail(slug):
    event = get_visible_or_404(db.session.scalar(select(Event).where(Event.slug == slug)))
    count_view(Event, event)
    now = now_local()

    dates = upcoming_dates(event, now, limit=6)
    finished = last_occurrence_end(event)
    is_past = not dates and (finished is None or finished < now)
    next_start, next_end = dates[0] if dates else (event.start_at, event.end_at)

    more = [o for o in first_per_event(find_occurrences(EventFilter(
        now, now + timedelta(days=90), organization_id=event.organization_id)))
        if o.event.id != event.id][:3]

    return render_template("public/event_detail.html", event=event, dates=dates, is_past=is_past,
                           next_start=next_start, next_end=next_end, more=more, now=now)


@bp.get("/veranstaltungen/<slug>/kalender.ics")
def event_ics(slug):
    event = get_visible_or_404(db.session.scalar(select(Event).where(Event.slug == slug)))
    url = url_for("public.event_detail", slug=slug, _external=True)
    body = event_to_ics(event, url=url, host=urlparse(url).hostname or "amberg-live")
    return Response(body, mimetype="text/calendar; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="{slug}.ics"',
    })
