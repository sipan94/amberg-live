"""Public pages: visibility rules, filters, recurring events, SEO files, privacy & security headers."""
import json
import re

from sqlalchemy import select

from app.extensions import db
from app.models import Category, Event, Status
from conftest import BROWSER


def slug_of(db_do, eid):
    return db_do(lambda: db.session.get(Event, eid).slug)


def test_main_pages_load(client, make):
    org = make.org(make.user())
    make.event(org)
    make.offer(org)
    for url in ["/", "/veranstaltungen", "/veranstaltungen/kalender", "/veranstaltungen/karte",
                "/angebote", "/geschaefte-vereine", "/merkliste", "/impressum", "/datenschutz",
                "/agb", "/kontakt", "/offline"]:
        assert client.get(url, headers=BROWSER).status_code == 200, url


def test_approved_event_visible_pending_hidden(client, make, db_do):
    org = make.org(make.user())
    public = make.event(org, title="Öffentlich")
    hidden = make.event(org, title="Geheim", status=Status.PENDING)
    listing = client.get("/veranstaltungen", headers=BROWSER).get_data(as_text=True)
    assert "Öffentlich" in listing and "Geheim" not in listing
    assert client.get(f"/veranstaltungen/{slug_of(db_do, public)}", headers=BROWSER).status_code == 200
    assert client.get(f"/veranstaltungen/{slug_of(db_do, hidden)}", headers=BROWSER).status_code == 404


def test_events_of_unapproved_or_blocked_orgs_are_hidden(client, make):
    pending_org = make.org(make.user("p@example.com"), name="Neu", status=Status.PENDING)
    blocked_org = make.org(make.user("b@example.com", blocked=True), name="Gesperrt")
    make.event(pending_org, title="Event von neuem Profil")
    make.event(blocked_org, title="Event von gesperrtem Nutzer")
    listing = client.get("/veranstaltungen", headers=BROWSER).get_data(as_text=True)
    assert "neuem Profil" not in listing and "gesperrtem" not in listing


def test_past_event_hidden_from_list_but_page_kept(client, make, db_do):
    org = make.org(make.user())
    past = make.event(org, title="Vorbei-Konzert", days=-10)
    assert "Vorbei-Konzert" not in client.get("/veranstaltungen", headers=BROWSER).get_data(as_text=True)
    page = client.get(f"/veranstaltungen/{slug_of(db_do, past)}", headers=BROWSER)
    assert page.status_code == 200 and "bereits stattgefunden" in page.get_data(as_text=True)


def test_weekly_event_appears_every_week(client, make):
    org = make.org(make.user())
    make.event(org, title="Wochenmarkt", days=-14, recurrence="weekly")
    listing = client.get("/veranstaltungen?zeitraum=monat", headers=BROWSER).get_data(as_text=True)
    assert listing.count("Wochenmarkt") >= 4  # once per week in the next 30 days


def test_filters_category_price_and_search(client, make, db_do):
    org = make.org(make.user())
    sport_id = db_do(lambda: db.session.scalar(select(Category.id).where(Category.slug == "sport")))
    make.event(org, title="Stadtlauf", category_id=sport_id)
    make.event(org, title="Teure Gala", is_free=False, price_info="99 €")

    def titles(query):
        return client.get(f"/veranstaltungen?{query}", headers=BROWSER).get_data(as_text=True)

    assert "Stadtlauf" in titles("kategorie=sport") and "Teure Gala" not in titles("kategorie=sport")
    assert "Teure Gala" in titles("preis=kostenpflichtig") and "Stadtlauf" not in titles("preis=kostenpflichtig")
    assert "Stadtlauf" in titles("q=stadt") and "Teure Gala" not in titles("q=stadt")


def test_invalid_filter_values_do_not_crash(client):
    for q in ["von=kaputt", "seite=9999", "kategorie=../../etc", "preis=<script>", "von=2026-12-01&bis=2026-11-01"]:
        assert client.get(f"/veranstaltungen?{q}", headers=BROWSER).status_code == 200


def test_featured_event_shown_as_top_tip(client, make):
    org = make.org(make.user())
    make.event(org, title="Hervorgehoben", is_featured=True)
    page = client.get("/veranstaltungen", headers=BROWSER).get_data(as_text=True)
    assert "Top-Tipps" in page and "Hervorgehoben" in page


def test_ics_download(client, make, db_do):
    eid = make.event(make.org(make.user()))
    r = client.get(f"/veranstaltungen/{slug_of(db_do, eid)}/kalender.ics", headers=BROWSER)
    assert r.mimetype == "text/calendar" and "attachment" in r.headers["Content-Disposition"]


def test_view_counter_ignores_bots(client, make, db_do):
    eid = make.event(make.org(make.user()))
    slug = slug_of(db_do, eid)
    client.get(f"/veranstaltungen/{slug}", headers=BROWSER)
    client.get(f"/veranstaltungen/{slug}", headers={"User-Agent": "Googlebot/2.1"})
    assert db_do(lambda: db.session.get(Event, eid).view_count) == 1


def test_event_json_ld(client, make, db_do):
    eid = make.event(make.org(make.user()))
    page = client.get(f"/veranstaltungen/{slug_of(db_do, eid)}", headers=BROWSER).get_data(as_text=True)
    data = json.loads(re.search(r'application/ld\+json">(.*?)</script>', page, re.S).group(1))
    assert data["@type"] == "Event"
    assert re.search(r"[+-]\d\d:\d\d$", data["startDate"])


def test_sitemap_robots_manifest_sw(client, make, db_do):
    org = make.org(make.user())
    public, hidden = make.event(org), make.event(org, status=Status.PENDING, title="Versteckt")
    sitemap = client.get("/sitemap.xml").get_data(as_text=True)
    assert slug_of(db_do, public) in sitemap and slug_of(db_do, hidden) not in sitemap
    assert "Disallow: /admin/" in client.get("/robots.txt").get_data(as_text=True)
    assert client.get("/manifest.webmanifest").get_json()["display"] == "standalone"
    assert client.get("/sw.js").mimetype == "application/javascript"


def test_favorites_api_only_returns_public_events(client, make, db_do):
    org = make.org(make.user())
    public, hidden = make.event(org), make.event(org, status=Status.PENDING)
    slugs = f"{slug_of(db_do, public)},{slug_of(db_do, hidden)}"
    data = client.get(f"/api/merkliste?slugs={slugs}").get_json()
    assert [item["slug"] for item in data] == [slug_of(db_do, public)]


def test_404_page(client):
    r = client.get("/gibt-es-nicht")
    assert r.status_code == 404 and "Seite nicht gefunden" in r.get_data(as_text=True)


def test_no_cookie_for_visitors_and_security_headers(client):
    r = client.get("/", headers=BROWSER)
    assert "Set-Cookie" not in r.headers  # → no cookie banner needed
    csp = r.headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_no_external_resources_in_html(client):
    """DSGVO: no fonts, scripts or styles from CDNs that would leak visitor IPs."""
    html = client.get("/", headers=BROWSER).get_data(as_text=True)
    external = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', html)
    assert [u for u in external if "localhost" not in u] == []
