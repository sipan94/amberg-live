"""Address -> coordinates with OpenStreetMap Nominatim (server-side, cached, failure-tolerant).

Nominatim's usage policy: max 1 request/second and an identifying User-Agent.
Saving a profile or event triggers at most one lookup, so we stay far below that.
"""
import json
import logging
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app

log = logging.getLogger(__name__)

# Rough box around Amberg and surroundings: rejects matches in another "Hauptstraße 1".
LAT_RANGE = (49.25, 49.65)
LNG_RANGE = (11.55, 12.15)


def geocode(address: str | None) -> tuple[float, float] | None:
    if not address or not current_app.config.get("GEOCODER_ENABLED"):
        return None
    query = address if "amberg" in address.lower() else f"{address}, Amberg"
    return _lookup(query.strip(), current_app.config["NOMINATIM_URL"], current_app.config["SITE_URL"])


@lru_cache(maxsize=256)
def _lookup(query: str, base_url: str, site_url: str) -> tuple[float, float] | None:
    url = f"{base_url}?{urlencode({'q': query, 'format': 'jsonv2', 'limit': 1, 'countrycodes': 'de'})}"
    request = Request(url, headers={"User-Agent": f"AmbergLive/1.0 (+{site_url})"})
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 (fixed https URL from config)
            results = json.load(response)
        lat, lng = float(results[0]["lat"]), float(results[0]["lon"])
    except (OSError, ValueError, KeyError, IndexError):
        log.warning("Geocoding failed for %r", query)
        return None
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LNG_RANGE[0] <= lng <= LNG_RANGE[1]):
        log.info("Geocoding result for %r is outside the Amberg area – ignored", query)
        return None
    return round(lat, 6), round(lng, 6)
