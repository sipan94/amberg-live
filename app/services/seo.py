"""schema.org JSON-LD for search engines (Google shows events with date and place in results)."""
from datetime import datetime

from flask import current_app, url_for

from ..utils.html import to_plain_text
from ..utils.timeutils import local_tz


def _iso(dt: datetime) -> str:
    """Local Amberg time with its UTC offset, e.g. 2026-11-14T19:30:00+01:00."""
    return dt.replace(tzinfo=local_tz()).isoformat()


def _abs(path: str) -> str:
    return current_app.config["SITE_URL"] + path


def _image(path: str | None) -> list[str]:
    from ..templating import asset, upload_url

    return [_abs(upload_url(path) if path else asset("img/og-default.png"))]


def _place(name, address, lat, lng) -> dict:
    place = {"@type": "Place", "name": name or address or "Amberg",
             "address": {"@type": "PostalAddress", "streetAddress": address or "",
                         "addressLocality": "Amberg", "postalCode": "92224",
                         "addressRegion": "Bayern", "addressCountry": "DE"}}
    if lat is not None and lng is not None:
        place["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng}
    return place


def event_jsonld(event, start: datetime, end: datetime | None) -> dict:
    url = _abs(url_for("public.event_detail", slug=event.slug))
    data = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": event.title,
        "description": to_plain_text(event.description, 500),
        "startDate": _iso(start),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": _place(event.location_name, event.address, event.lat, event.lng),
        "image": _image(event.image),
        "url": url,
        "isAccessibleForFree": event.is_free,
        "organizer": {"@type": "Organization", "name": event.organization.name,
                      "url": _abs(url_for("public.organization_detail", slug=event.organization.slug))},
    }
    if end:
        data["endDate"] = _iso(end)
    if event.is_free:
        data["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "EUR",
                          "availability": "https://schema.org/InStock", "url": url}
    return data


def organization_jsonld(org) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "Organization" if org.is_club else "LocalBusiness",
        "name": org.name,
        "description": to_plain_text(org.description, 500),
        "url": _abs(url_for("public.organization_detail", slug=org.slug)),
        "image": _image(org.logo or org.cover_image),
        "address": _place(None, org.address, None, None)["address"],
    }
    if org.lat is not None:
        data["geo"] = {"@type": "GeoCoordinates", "latitude": org.lat, "longitude": org.lng}
    if org.phone:
        data["telephone"] = org.phone
    if org.website:
        data["sameAs"] = [org.website]
    return data


def website_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": current_app.config["SITE_NAME"],
        "url": _abs("/"),
        "inLanguage": "de-DE",
        "potentialAction": {
            "@type": "SearchAction",
            "target": _abs(url_for("public.events")) + "?q={search_term_string}",
            "query-input": "required name=search_term_string",
        },
    }

