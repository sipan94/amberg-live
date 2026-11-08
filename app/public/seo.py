"""PWA (manifest, service worker, offline page) and SEO files (robots.txt, sitemap.xml)."""
from flask import Response, current_app, jsonify, redirect, render_template, url_for
from sqlalchemy import or_, select

from ..extensions import db, limiter
from ..i18n import t
from ..models import Offer, Organization, Status, User
from ..services.events import public_events
from ..templating import asset, asset_version
from ..utils.timeutils import today_local
from . import bp


@bp.get("/manifest.webmanifest")
@limiter.exempt
def manifest():
    data = {
        "name": t("site.name"),
        "short_name": t("site.name"),
        "description": t("site.description"),
        "lang": "de",
        "start_url": "/?quelle=app",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f6f5f2",
        "theme_color": "#f6f5f2",
        "categories": ["events", "lifestyle", "travel"],
        "icons": [
            {"src": asset("img/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": asset("img/icon-512.png"), "sizes": "512x512", "type": "image/png"},
            {"src": asset("img/icon-maskable-512.png"), "sizes": "512x512", "type": "image/png",
             "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": t("home.today"), "url": url_for("public.events", zeitraum="heute")},
            {"name": t("nav.map"), "url": url_for("public.events_map")},
            {"name": t("nav.favorites"), "url": url_for("public.favorites")},
        ],
    }
    response = jsonify(data)
    response.mimetype = "application/manifest+json"
    return response


@bp.get("/sw.js")
@limiter.exempt
def service_worker():
    """Served from the root so the worker may control the whole site."""
    precache = [url_for("public.offline"), asset("css/app.css"), asset("js/app.js"),
                asset("js/theme-init.js"), asset("js/map.js"), asset("img/icon-192.png")]
    body = render_template("pwa/sw.js", version=asset_version(), precache=precache)
    return Response(body, mimetype="application/javascript", headers={
        "Cache-Control": "no-cache",  # browsers must always check for a new worker
        "Service-Worker-Allowed": "/",
    })


@bp.get("/offline")
@limiter.exempt
def offline():
    return render_template("pwa/offline.html")


@bp.get("/favicon.ico")
@limiter.exempt
def favicon():
    return redirect(asset("img/favicon.ico"), code=301)


@bp.get("/robots.txt")
@limiter.exempt
def robots():
    lines = [
        "User-agent: *",
        "Disallow: /konto/",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /anmelden",
        "Disallow: /registrieren",
        "Disallow: /passwort-",
        "Disallow: /bestaetigen/",
        "Disallow: /merkliste",
        "Allow: /",
        "",
        f"Sitemap: {current_app.config['SITE_URL']}{url_for('public.sitemap')}",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@bp.get("/sitemap.xml")
@limiter.exempt
def sitemap():
    """All public pages. Past events stay listed: their pages are kept for search engines."""
    base = current_app.config["SITE_URL"]
    entries = [(url_for(e), None, "daily") for e in
               ("public.home", "public.events", "public.events_calendar", "public.offers",
                "public.organizations")]
    entries += [(url_for("public.legal", page=p), None, "yearly") for p in ("impressum", "datenschutz", "agb", "kontakt")]

    for ev in db.session.scalars(public_events()):
        entries.append((url_for("public.event_detail", slug=ev.slug), ev.updated_at, "weekly"))
    today = today_local()
    offers = db.session.scalars(
        select(Offer).join(Offer.organization).join(Organization.owner)
        .where(Offer.status == Status.APPROVED, Organization.status == Status.APPROVED,
               User.is_blocked.is_(False), or_(Offer.valid_until.is_(None), Offer.valid_until >= today)))
    entries += [(url_for("public.offer_detail", slug=o.slug), o.updated_at, "weekly") for o in offers]
    orgs = db.session.scalars(select(Organization).join(Organization.owner).where(
        Organization.status == Status.APPROVED, User.is_blocked.is_(False)))
    entries += [(url_for("public.organization_detail", slug=o.slug), o.updated_at, "weekly") for o in orgs]

    xml = render_template("pwa/sitemap.xml", entries=entries, base=base)
    return Response(xml, mimetype="application/xml")
