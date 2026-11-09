"""Public data for the app – same rules as the website (only approved content, past events
hidden from lists, recurring events expanded, highlights first)."""
import calendar as pycal
from datetime import date, timedelta
from itertools import groupby

from flask import abort, jsonify, request, url_for
from sqlalchemy import or_, select

from ..extensions import db, limiter
from ..i18n import t
from ..models import WEEKDAYS, Category, Event, Offer, Organization, OrgType
from ..public.helpers import count_view, parse_event_filter
from ..public.organizations import TYPE_PARAM, public_orgs
from ..services.events import (EventFilter, Occurrence, day_start, find_occurrences, first_per_event,
                               highlight_sort_key, last_occurrence_end, today_window, upcoming_dates,
                               weekend_window)
from ..services.offers import current_offers_query
from ..services.pagination import ListPagination
from ..services.stats import track
from ..templating import date_short
from ..utils.html import to_plain_text
from ..utils.timeutils import now_local, today_local
from . import bp, page_meta
from . import serializers as ser

EVENTS_PER_PAGE = 20


@bp.get("/meta")
def api_meta():
    """Everything the app needs once at start: categories, filter choices, legal pages."""
    cats = db.session.scalars(select(Category).order_by(Category.sort_order)).all()
    return jsonify(
        site_name=t("site.name"),
        categories=[ser.category(c) for c in cats],
        periods=[{"value": v, "label": t(f"events.period_{k}")} for v, k in
                 [("alle", "all"), ("heute", "today"), ("wochenende", "weekend"), ("woche", "week"), ("monat", "month")]],
        prices=[{"value": "", "label": t("events.price_all")},
                {"value": "kostenlos", "label": t("events.price_free")},
                {"value": "kostenpflichtig", "label": t("events.price_paid")}],
        legal={p: url_for("public.legal", page=p, _external=True) for p in ("impressum", "datenschutz", "agb", "kontakt")},
        web_url=url_for("public.home", _external=True),
    )


@bp.get("/home")
def api_home():
    now = now_local()
    start, today_end = today_window(now)
    today = sorted(find_occurrences(EventFilter(start, today_end)), key=highlight_sort_key)

    w_start, w_end = weekend_window(now)
    w_start = max(w_start, today_end)
    label = "home.weekend"
    if w_start >= w_end:
        w_start, w_end = weekend_window(now + timedelta(days=5))
        label = "home.next_weekend"
    weekend = sorted(first_per_event(find_occurrences(EventFilter(w_start, w_end))), key=highlight_sort_key)
    upcoming = first_per_event(find_occurrences(EventFilter(w_end, w_end + timedelta(days=30))))[:8]
    offers = db.session.scalars(current_offers_query().limit(4)).all()
    track("app:home")
    today_date = now.date()
    return jsonify(
        today_label=date_short(today_date),
        today=[ser.occurrence(o, now) for o in today[:10]],
        weekend_title=t(label),
        weekend=[ser.occurrence(o, now) for o in weekend[:10]],
        upcoming=[ser.occurrence(o, now) for o in upcoming],
        offers=[ser.offer(o, today_date) for o in offers],
    )


@bp.get("/events")
def api_events():
    now = now_local()
    f, state = parse_event_filter(request.args, now)
    occurrences = find_occurrences(f)
    page = ListPagination(occurrences, request.args.get("seite", 1, type=int), EVENTS_PER_PAGE)
    tips = first_per_event([o for o in occurrences if o.is_highlight])[:3] if page.page == 1 else []
    days = [{"date": d.isoformat(), "label": date_short(d), "items": [ser.occurrence(o, now) for o in items]}
            for d, items in groupby(page.items, key=lambda o: o.start.date())]
    return jsonify(tips=[ser.occurrence(o, now) for o in tips], days=days, filter={
        "period": state["period"], "category": state["category"], "price": state["price"], "q": state["q"],
        "von": state["von"].isoformat() if state["von"] else None,
        "bis": state["bis"].isoformat() if state["bis"] else None,
    }, **page_meta(page))


@bp.get("/events/calendar")
def api_calendar():
    now = now_local()
    try:
        year, month = map(int, request.args.get("monat", "").split("-"))
        first = date(year, month, 1)
    except ValueError:
        first = now.date().replace(day=1)
    _, state = parse_event_filter(request.args, now)
    last = first.replace(day=pycal.monthrange(first.year, first.month)[1])
    start = max(day_start(first), now.replace(hour=0, minute=0, second=0))
    f = EventFilter(start=start, end=day_start(last + timedelta(days=1)),
                    category=state["category"], price=state["price"], q=state["q"] or None)
    by_day: dict[str, list] = {}
    for occ in find_occurrences(f) if f.start < f.end else []:
        end_day = (occ.end - timedelta(seconds=1)).date() if occ.end and occ.end > occ.start else occ.start.date()
        d = max(occ.start.date(), first)
        while d <= min(end_day, last):
            by_day.setdefault(d.isoformat(), []).append(ser.occurrence(occ, now))
            d += timedelta(days=1)
    prev_month = (first - timedelta(days=1)).replace(day=1)
    next_month = last + timedelta(days=1)
    return jsonify(month=first.strftime("%Y-%m"), title=f"{t('dates.months')[first.month - 1]} {first.year}",
                   prev=prev_month.strftime("%Y-%m"), next=next_month.strftime("%Y-%m"),
                   weekdays=t("dates.weekdays_short"), first_weekday=first.weekday(),
                   days_in_month=last.day, today=now.date().isoformat(), days=by_day)


@bp.get("/events/map")
def api_map():
    now = now_local()
    f, _ = parse_event_filter(request.args, now)
    occs = first_per_event(find_occurrences(f))
    with_coords = [o for o in occs if o.event.lat is not None and o.event.lng is not None]
    return jsonify(markers=[ser.occurrence(o, now) for o in with_coords],
                   missing=len(occs) - len(with_coords),
                   tiles={"url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                          "attribution": t("map.attribution")},
                   center={"lat": 49.4448, "lng": 11.8581})


@bp.get("/events/<slug>")
def api_event(slug):
    event = db.session.scalar(select(Event).where(Event.slug == slug))
    if event is None or not event.is_public:
        abort(404)
    count_view(Event, event)
    now = now_local()
    dates = upcoming_dates(event, now, limit=6)
    finished = last_occurrence_end(event)
    is_past = not dates and (finished is None or finished < now)
    next_start, next_end = dates[0] if dates else (event.start_at, event.end_at)
    more = [o for o in first_per_event(find_occurrences(EventFilter(
        now, now + timedelta(days=90), organization_id=event.organization_id))) if o.event.id != event.id][:3]
    return jsonify(ser.event_detail(event, next_start, next_end, dates, is_past, more))


@bp.get("/offers")
def api_offers():
    page = db.paginate(current_offers_query(), page=request.args.get("seite", 1, type=int),
                       per_page=12, error_out=False)
    today = today_local()
    return jsonify(items=[ser.offer(o, today) for o in page.items], **page_meta(page))


@bp.get("/offers/<slug>")
def api_offer(slug):
    offer = db.session.scalar(select(Offer).where(Offer.slug == slug))
    if offer is None or not offer.is_public:
        abort(404)
    count_view(Offer, offer)
    return jsonify(ser.offer(offer, today_local()))


@bp.get("/organizations")
def api_organizations():
    typ = request.args.get("typ", "")
    q = " ".join(request.args.get("q", "").split())[:100]
    stmt = public_orgs()
    if typ in TYPE_PARAM:
        stmt = stmt.where(Organization.org_type == TYPE_PARAM[typ])
    if q:
        stmt = stmt.where(or_(Organization.name.icontains(q, autoescape=True),
                              Organization.description.icontains(q, autoescape=True)))
    page = db.paginate(stmt.order_by(Organization.is_premium.desc(), Organization.name),
                       page=request.args.get("seite", 1, type=int), per_page=18, error_out=False)
    return jsonify(items=[ser.org_brief(o) | {"summary": to_plain_text(o.description, 140),
                                              "type_label": t("badges.club") if o.org_type == OrgType.CLUB else t("badges.business")}
                          for o in page.items], **page_meta(page))


@bp.get("/organizations/<slug>")
def api_organization(slug):
    org = db.session.scalar(select(Organization).where(Organization.slug == slug))
    if org is None or not org.is_public:
        abort(404)
    track(f"organization:{org.id}")
    now = now_local()
    events = first_per_event(find_occurrences(EventFilter(now, now + timedelta(days=180), organization_id=org.id)))[:12]
    today = now.date()
    offers = [o for o in org.offers if o.is_approved and (o.valid_until is None or o.valid_until >= today)]
    return jsonify(ser.organization(org, WEEKDAYS) | {
        "events": [ser.occurrence(o, now) for o in events],
        "offers": [ser.offer(o, today) for o in offers],
    })


@bp.post("/favorites")
@limiter.limit("60/minute")
def api_favorites():
    """Card data for event slugs the app keeps on the phone (like the website's Merkliste)."""
    slugs = [s for s in ((request.get_json(silent=True) or {}).get("slugs") or []) if isinstance(s, str)][:100]
    now = now_local()
    result = []
    for event in db.session.scalars(select(Event).where(Event.slug.in_(slugs))):
        if not event.is_public:
            continue
        dates = upcoming_dates(event, now, limit=1)
        start, end = dates[0] if dates else (event.start_at, event.end_at)
        result.append(ser.occurrence(Occurrence(event, start, end), now) | {"past": not dates})
    result.sort(key=lambda r: (r["past"], r["start"]))
    return jsonify(items=result)
