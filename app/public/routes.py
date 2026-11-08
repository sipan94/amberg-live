"""Home page, favorites, uploads, legal placeholders, health check."""
from datetime import timedelta

from flask import abort, current_app, jsonify, render_template, request, send_from_directory, url_for
from sqlalchemy import select, text

from ..extensions import db, limiter
from ..models import Event
from ..services.events import (EventFilter, find_occurrences, first_per_event, highlight_sort_key,
                               today_window, upcoming_dates, weekend_window)
from ..services.offers import current_offers_query
from ..services.stats import track
from ..templating import format_when
from ..utils.timeutils import now_local
from . import bp


@bp.get("/")
def home():
    now = now_local()

    today_start, today_end = today_window(now)
    today = sorted(find_occurrences(EventFilter(today_start, today_end)), key=highlight_sort_key)

    # Weekend without today's items. On Sunday, show next weekend instead of nothing.
    weekend_start, weekend_end = weekend_window(now)
    weekend_start = max(weekend_start, today_end)
    weekend_label = "home.weekend"
    if weekend_start >= weekend_end:
        weekend_start, weekend_end = weekend_window(now + timedelta(days=5))
        weekend_label = "home.next_weekend"
    weekend = sorted(first_per_event(find_occurrences(EventFilter(weekend_start, weekend_end))),
                     key=highlight_sort_key)

    upcoming = first_per_event(find_occurrences(
        EventFilter(weekend_end, weekend_end + timedelta(days=30))))[:8]

    offers = db.session.scalars(current_offers_query().limit(4)).all()
    track("page:home")

    return render_template(
        "public/home.html", today=today, weekend=weekend, weekend_label=weekend_label,
        upcoming=upcoming, offers=offers,
    )


@bp.get("/merkliste")
def favorites():
    return render_template("public/favorites.html")


@bp.get("/api/merkliste")
@limiter.limit("60/minute")
def favorites_data():
    """Card data for event slugs saved in the visitor's localStorage."""
    slugs = [s for s in request.args.get("slugs", "").split(",") if s][:50]
    if not slugs:
        return jsonify([])
    now = now_local()
    events = db.session.scalars(select(Event).where(Event.slug.in_(slugs))).all()
    result = []
    for event in events:
        if not event.is_public:
            continue
        upcoming = upcoming_dates(event, now, limit=1)
        start, end = upcoming[0] if upcoming else (event.start_at, event.end_at)
        result.append({
            "slug": event.slug,
            "title": event.title,
            "url": url_for("public.event_detail", slug=event.slug),
            "when": format_when(start, end),
            "location": event.location_name or "",
            "past": not upcoming,
            "color": event.category.color if event.category else "#64748b",
            "sort": start.isoformat(),
        })
    result.sort(key=lambda r: (r["past"], r["sort"]))
    return jsonify(result)


@bp.get("/uploads/<path:filename>")
def uploaded_file(filename):
    # In production nginx serves /uploads directly; this is the development fallback.
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, max_age=31536000)


LEGAL_PAGES = {
    "impressum": "footer.impressum",
    "datenschutz": "footer.privacy",
    "agb": "footer.terms",
    "kontakt": "footer.contact",
}


@bp.get("/<any(impressum, datenschutz, agb, kontakt):page>")
def legal(page):
    # Legal texts are long-form content per language: templates/legal/<page>.html
    if page not in LEGAL_PAGES:
        abort(404)
    return render_template(f"legal/{page}.html", page=page, title_key=LEGAL_PAGES[page])


@bp.get("/healthz")
@limiter.exempt
def healthz():
    """Used by monitoring / the deploy script to check app and database."""
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok")
