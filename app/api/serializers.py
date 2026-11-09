"""Turn models into JSON for the app. Labels (dates, prices) are formatted on the server
so the app shows exactly the same German texts as the website."""
from datetime import date, datetime

from flask import url_for

from ..i18n import t
from ..services.images import small_variant
from ..templating import format_price, format_when
from ..utils.html import html_to_text, sanitize_html


def iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


def image(path: str | None) -> dict | None:
    if not path:
        return None
    return {"url": url_for("public.uploaded_file", filename=path, _external=True),
            "small": url_for("public.uploaded_file", filename=small_variant(path), _external=True)}


def category(c) -> dict | None:
    if c is None:
        return None
    return {"id": c.id, "name": c.name, "slug": c.slug, "icon": c.icon, "color": c.color}


def org_brief(o) -> dict:
    return {"id": o.id, "slug": o.slug, "name": o.name, "type": o.org_type,
            "is_premium": o.is_premium, "logo": image(o.logo)}


def occurrence(occ, now: datetime | None = None) -> dict:
    """One dated appearance of an event (recurring events have many)."""
    ev = occ.event
    return {
        "id": ev.id,
        "slug": ev.slug,
        "title": ev.title,
        "start": iso(occ.start),
        "end": iso(occ.end),
        "when": format_when(occ.start, occ.end),
        "ongoing": bool(now and occ.is_ongoing(now)),
        "category": category(ev.category),
        "location_name": ev.location_name,
        "lat": ev.lat,
        "lng": ev.lng,
        "is_free": ev.is_free,
        "price": format_price(ev),
        "is_featured": ev.is_featured,
        "is_premium": ev.organization.is_premium,
        "is_highlight": occ.is_highlight,
        "recurrence": ev.recurrence,
        "image": image(ev.image),
        "organization": org_brief(ev.organization),
    }


def event_detail(ev, next_start, next_end, dates, is_past: bool, more) -> dict:
    web_url = url_for("public.event_detail", slug=ev.slug, _external=True)
    return {
        "id": ev.id,
        "slug": ev.slug,
        "title": ev.title,
        "description_html": sanitize_html(ev.description),
        "description_text": html_to_text(ev.description),
        "start": iso(next_start),
        "end": iso(next_end),
        "when": format_when(next_start, next_end),
        "recurrence": ev.recurrence,
        "recurrence_label": {"weekly": t("events.weekly"), "monthly": t("events.monthly")}.get(ev.recurrence),
        "recurrence_until": iso(ev.recurrence_until),
        "next_dates": [{"start": iso(s), "end": iso(e), "when": format_when(s, e)} for s, e in dates],
        "is_past": is_past,
        "location_name": ev.location_name,
        "address": ev.address,
        "lat": ev.lat,
        "lng": ev.lng,
        "is_free": ev.is_free,
        "price": format_price(ev),
        "category": category(ev.category),
        "is_featured": ev.is_featured,
        "image": image(ev.image),
        "organization": org_brief(ev.organization),
        "web_url": web_url,
        "ics_url": url_for("public.event_ics", slug=ev.slug, _external=True),
        "share_text": f"{ev.title} – {web_url}",
        "more_from_organizer": [occurrence(o) for o in more],
    }


def offer(o, today: date) -> dict:
    if o.valid_until:
        validity = t("offers.valid_until", date=o.valid_until.strftime("%d.%m.%Y"))
    else:
        validity = t("offers.valid_open")
    if o.valid_from > today:
        validity = t("offers.valid_from", date=o.valid_from.strftime("%d.%m.")) + " · " + validity
    return {
        "id": o.id,
        "slug": o.slug,
        "title": o.title,
        "description_html": sanitize_html(o.description),
        "description_text": html_to_text(o.description),
        "valid_from": iso(o.valid_from),
        "valid_until": iso(o.valid_until),
        "validity": validity,
        "is_expired": bool(o.valid_until and o.valid_until < today),
        "is_featured": o.is_featured,
        "image": image(o.image),
        "organization": org_brief(o.organization),
        "web_url": url_for("public.offer_detail", slug=o.slug, _external=True),
    }


def organization(o, weekdays) -> dict:
    hours = [{"day": d, "label": t("dates.weekday_keys")[d], "value": (o.opening_hours or {})[d]}
             for d in weekdays if (o.opening_hours or {}).get(d)]
    return {
        **org_brief(o),
        "description_html": sanitize_html(o.description),
        "description_text": html_to_text(o.description),
        "address": o.address,
        "lat": o.lat,
        "lng": o.lng,
        "phone": o.phone,
        "email": o.email,
        "website": o.website,
        "opening_hours": hours,
        "cover_image": image(o.cover_image),
        "web_url": url_for("public.organization_detail", slug=o.slug, _external=True),
    }


def moderation_fields(item) -> dict:
    return {"status": item.status, "status_label": t(f"status.{item.status}"),
            "rejection_reason": item.rejection_reason}


def my_event(ev) -> dict:
    return {
        "id": ev.id, "slug": ev.slug, "title": ev.title,
        "start": iso(ev.start_at), "end": iso(ev.end_at),
        "when": format_when(ev.start_at, ev.end_at),
        "recurrence": ev.recurrence, "recurrence_until": iso(ev.recurrence_until),
        "category_id": ev.category_id, "location_name": ev.location_name, "address": ev.address,
        "is_free": ev.is_free, "price_info": ev.price_info,
        "description_text": html_to_text(ev.description),
        "image": image(ev.image), "is_featured": ev.is_featured, "view_count": ev.view_count,
        **moderation_fields(ev),
    }


def my_offer(o) -> dict:
    return {
        "id": o.id, "slug": o.slug, "title": o.title,
        "valid_from": iso(o.valid_from), "valid_until": iso(o.valid_until),
        "description_text": html_to_text(o.description),
        "image": image(o.image), "view_count": o.view_count,
        **moderation_fields(o),
    }


def my_organization(o, weekdays) -> dict:
    return {
        **organization(o, weekdays),
        "opening_hours_raw": {d: (o.opening_hours or {}).get(d, "") for d in weekdays},
        **moderation_fields(o),
    }


def user(u, org=None) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role, "is_admin": u.is_admin,
            "is_verified": u.is_verified, "organization": org_brief(org) | moderation_fields(org) if org else None}
