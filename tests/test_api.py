"""JSON API for the mobile app (/api/v1): tokens, public data, business area, admin."""
from datetime import timedelta
from pathlib import Path

from app.extensions import db
from app.models import ApiToken, Event, Offer, Organization, Role, Status, User
from app.services import mail
from app.utils.timeutils import now_local, utcnow
from conftest import PASSWORD, image_bytes

API = "/api/v1"


def api_login(client, email, password=PASSWORD):
    r = client.post(f"{API}/auth/login", json={"email": email, "password": password, "device": "pytest"})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def event_json(**overrides):
    tomorrow = (now_local() + timedelta(days=1)).date().isoformat()
    data = {"title": "App-Konzert", "category_id": 1, "description": "Live-Musik", "start_date": tomorrow,
            "start_time": "19:00", "recurrence": "none", "location_name": "Saal", "is_free": True,
            "rights_confirmed": True}
    data.update(overrides)
    return data


# ---- auth & tokens ------------------------------------------------------------------------

def test_login_returns_token_and_stores_only_hash(client, make, db_do):
    make.user("owner@example.com")
    headers = api_login(client, "owner@example.com")
    plain = headers["Authorization"][7:]
    stored = db_do(lambda: db.session.scalars(db.select(ApiToken.token_hash)).all())
    assert len(stored) == 1 and plain not in stored[0]  # only the SHA-256 hash is saved
    me = client.get(f"{API}/auth/me", headers=headers).get_json()
    assert me["email"] == "owner@example.com"


def test_wrong_password_and_unknown_email_look_the_same(client, make):
    make.user("owner@example.com")
    wrong = client.post(f"{API}/auth/login", json={"email": "owner@example.com", "password": "falsch-falsch"})
    unknown = client.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": "falsch-falsch"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


def test_login_validation_errors_are_german_json(client):
    r = client.post(f"{API}/auth/login", json={"email": "kein-email", "password": ""})
    assert r.status_code == 422
    body = r.get_json()
    assert "email" in body["fields"] and "password" in body["fields"]


def test_blocked_user_cannot_log_in(client, make):
    make.user("b@example.com", blocked=True)
    r = client.post(f"{API}/auth/login", json={"email": "b@example.com", "password": PASSWORD})
    assert r.status_code == 403 and r.get_json()["code"] == "blocked"


def test_missing_bad_and_expired_tokens(client, make, db_do):
    make.user("owner@example.com")
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Bearer unsinn"}).status_code == 401
    headers = api_login(client, "owner@example.com")

    def expire():
        db.session.execute(db.update(ApiToken).values(expires_at=utcnow() - timedelta(minutes=1)))
        db.session.commit()
    db_do(expire)
    assert client.get(f"{API}/auth/me", headers=headers).status_code == 401


def test_api_ignores_the_browser_session_cookie(client, owner):
    """`owner` is logged in on the website with this client – the API must not accept that."""
    assert client.get(f"{API}/me/overview").status_code == 401


def test_logout_revokes_only_this_token(client, make):
    make.user("owner@example.com")
    phone, tablet = api_login(client, "owner@example.com"), api_login(client, "owner@example.com")
    assert client.post(f"{API}/auth/logout", headers=phone).status_code == 200
    assert client.get(f"{API}/auth/me", headers=phone).status_code == 401
    assert client.get(f"{API}/auth/me", headers=tablet).status_code == 200


def test_change_password_logs_out_other_devices(client, make):
    make.user("owner@example.com")
    phone, tablet = api_login(client, "owner@example.com"), api_login(client, "owner@example.com")
    r = client.post(f"{API}/auth/change-password", headers=phone, json={
        "current_password": PASSWORD, "password": "neues-passwort-456", "password2": "neues-passwort-456"})
    assert r.status_code == 200, r.get_json()
    assert client.get(f"{API}/auth/me", headers=phone).status_code == 200
    assert client.get(f"{API}/auth/me", headers=tablet).status_code == 401


def test_web_password_change_logs_out_the_app(client, make):
    from conftest import login

    make.user("owner@example.com")
    headers = api_login(client, "owner@example.com")
    web = client.application.test_client()
    login(web, "owner@example.com")
    web.post("/konto/einstellungen", data={"current_password": PASSWORD, "password": "neues-passwort-456",
                                           "password2": "neues-passwort-456"})
    assert client.get(f"{API}/auth/me", headers=headers).status_code == 401


def test_register_does_not_reveal_existing_accounts(client, make):
    make.user("owner@example.com")
    new = client.post(f"{API}/auth/register", json={
        "email": "neu@example.com", "password": PASSWORD, "password2": PASSWORD, "accept_terms": True})
    existing = client.post(f"{API}/auth/register", json={
        "email": "owner@example.com", "password": PASSWORD, "password2": PASSWORD, "accept_terms": True})
    assert new.status_code == existing.status_code == 201, (new.get_json(), existing.get_json())
    assert new.get_json() == existing.get_json()
    assert len(mail.outbox) == 2  # a verify mail and an "already registered" mail


def test_delete_account_from_app(client, make, db_do):
    user_id = make.user("owner@example.com")
    make.event(make.org(user_id))
    headers = api_login(client, "owner@example.com")
    assert client.post(f"{API}/auth/delete-account", headers=headers,
                       json={"password": "falsch-falsch", "confirm": True}).status_code == 422
    r = client.post(f"{API}/auth/delete-account", headers=headers, json={"password": PASSWORD, "confirm": True})
    assert r.status_code == 200, r.get_json()
    assert db_do(lambda: (db.session.get(User, user_id), db.session.query(Event).count())) == (None, 0)


# ---- public data ----------------------------------------------------------------------------

def test_public_lists_show_only_approved_content(client, make):
    org = make.org(make.user())
    make.event(org, title="Sichtbar")
    make.event(org, title="Geheim", status=Status.PENDING)
    make.offer(org, title="Rabatt")
    events = client.get(f"{API}/events?zeitraum=alle").get_json()
    titles = [i["title"] for d in events["days"] for i in d["items"]]
    assert "Sichtbar" in titles and "Geheim" not in titles
    assert [o["title"] for o in client.get(f"{API}/offers").get_json()["items"]] == ["Rabatt"]
    assert client.get(f"{API}/home").status_code == 200
    meta = client.get(f"{API}/meta").get_json()
    assert meta["categories"] and meta["legal"]["impressum"].startswith("http")


def test_event_detail_and_hidden_event(client, make, db_do):
    org = make.org(make.user())
    ok = make.event(org, title="Offen")
    hidden = make.event(org, title="Wartet", status=Status.PENDING)
    slug_ok, slug_hidden = db_do(lambda: (db.session.get(Event, ok).slug, db.session.get(Event, hidden).slug))
    detail = client.get(f"{API}/events/{slug_ok}").get_json()
    assert detail["title"] == "Offen" and detail["ics_url"].startswith("http")
    r = client.get(f"{API}/events/{slug_hidden}")
    assert r.status_code == 404 and "error" in r.get_json()


def test_calendar_map_and_organizations(client, make):
    org = make.org(make.user(), name="Musikverein")
    make.event(org, lat=49.44, lng=11.86)
    assert client.get(f"{API}/events/calendar").get_json()["days"]
    assert len(client.get(f"{API}/events/map?zeitraum=alle").get_json()["markers"]) == 1
    orgs = client.get(f"{API}/organizations").get_json()["items"]
    assert [o["name"] for o in orgs] == ["Musikverein"]


def test_favorites_skip_unknown_and_hidden(client, make, db_do):
    org = make.org(make.user())
    ok, hidden = make.event(org, title="Merken"), make.event(org, title="Nein", status=Status.REJECTED)
    slugs = db_do(lambda: [db.session.get(Event, i).slug for i in (ok, hidden)])
    items = client.post(f"{API}/favorites", json={"slugs": slugs + ["gibt-es-nicht", 42]}).get_json()["items"]
    assert [i["title"] for i in items] == ["Merken"]


def test_unknown_api_path_is_json_404(client):
    r = client.get(f"{API}/gibt-es-nicht")
    assert r.status_code == 404 and r.is_json


# ---- business area -----------------------------------------------------------------------------

def test_create_event_goes_to_review(client, make, db_do):
    org_id = make.org(make.user("owner@example.com"))
    headers = api_login(client, "owner@example.com")
    r = client.post(f"{API}/me/events", headers=headers, json=event_json())
    assert r.status_code == 201, r.get_json()
    assert r.get_json()["pending"] is True
    ev = db_do(lambda: db.session.query(Event).filter_by(title="App-Konzert").one())
    assert ev.status == Status.PENDING and ev.organization_id == org_id
    assert "Neu: Veranstaltung" in mail.outbox[-1]["Subject"]


def test_event_validation_errors_per_field(client, make):
    make.org(make.user("owner@example.com"))
    headers = api_login(client, "owner@example.com")
    r = client.post(f"{API}/me/events", headers=headers, json=event_json(rights_confirmed=False))
    assert r.status_code == 422 and "rights_confirmed" in r.get_json()["fields"]
    # Date rules run after the single-field checks, like on the website.
    r = client.post(f"{API}/me/events", headers=headers, json=event_json(start_date="2020-01-01"))
    assert r.status_code == 422 and "Vergangenheit" in " ".join(r.get_json()["fields"]["start_date"])


def test_unverified_and_profileless_users(client, make):
    make.user("u@example.com", verified=False)
    make.user("n@example.com")
    r = client.post(f"{API}/me/events", headers=api_login(client, "u@example.com"), json=event_json())
    assert r.status_code == 403 and r.get_json()["code"] == "not_verified"
    r = client.post(f"{API}/me/events", headers=api_login(client, "n@example.com"), json=event_json())
    assert r.status_code == 409 and r.get_json()["code"] == "no_profile"


def test_create_organization_profile(client, make, db_do):
    make.user("owner@example.com")
    headers = api_login(client, "owner@example.com")
    r = client.post(f"{API}/me/organization", headers=headers, json={
        "name": "Café Vils", "org_type": "business", "description": "Kaffee am Fluss", "rights_confirmed": True})
    assert r.status_code == 201, r.get_json()
    assert db_do(lambda: db.session.query(Organization).one().status) == Status.PENDING


def test_users_cannot_touch_foreign_content(client, make):
    make.org(make.user("owner@example.com"))
    foreign = make.event(make.org(make.user("fremd@example.com"), name="Fremd"))
    headers = api_login(client, "owner@example.com")
    assert client.get(f"{API}/me/events/{foreign}", headers=headers).status_code == 404
    assert client.delete(f"{API}/me/events/{foreign}", headers=headers).status_code == 404
    assert client.put(f"{API}/me/events/{foreign}", headers=headers, json=event_json()).status_code == 404


def test_editing_title_needs_review_again(client, make, db_do):
    org = make.org(make.user("owner@example.com"))
    ev = make.event(org)
    headers = api_login(client, "owner@example.com")
    item = client.get(f"{API}/me/events/{ev}", headers=headers).get_json()
    assert item["status"] == Status.APPROVED
    r = client.put(f"{API}/me/events/{ev}", headers=headers, json=event_json(title="Neuer Titel"))
    assert r.status_code == 200 and r.get_json()["pending"] is True
    assert db_do(lambda: db.session.get(Event, ev).status) == Status.PENDING


def test_offer_with_image_upload_strips_exif(client, make, db_do, app):
    make.org(make.user("owner@example.com"))
    headers = api_login(client, "owner@example.com")
    today = now_local().date().isoformat()
    r = client.post(f"{API}/me/offers", headers=headers, content_type="multipart/form-data", data={
        "title": "Frühstück -20 %", "description": "Jeden Morgen", "valid_from": today,
        "rights_confirmed": "y", "image": (image_bytes(), "foto.jpg")})
    assert r.status_code == 201, r.get_json()
    item = r.get_json()["item"]
    assert item["image"]["url"].endswith(".webp")
    filename = db_do(lambda: db.session.query(Offer).one().image)
    saved = Path(app.config["UPLOAD_FOLDER"]) / filename
    assert saved.exists() and b"Secret Phone" not in saved.read_bytes()


def test_bad_image_is_a_field_error(client, make):
    make.org(make.user("owner@example.com"))
    headers = api_login(client, "owner@example.com")
    import io
    r = client.post(f"{API}/me/offers", headers=headers, content_type="multipart/form-data", data={
        "title": "Kaputt", "description": "x", "valid_from": now_local().date().isoformat(),
        "rights_confirmed": "y", "image": (io.BytesIO(b"kein bild"), "foto.jpg")})
    assert r.status_code == 422 and "image" in r.get_json()["fields"]


def test_delete_own_event(client, make, db_do):
    ev = make.event(make.org(make.user("owner@example.com")))
    headers = api_login(client, "owner@example.com")
    assert client.delete(f"{API}/me/events/{ev}", headers=headers).status_code == 200
    assert db_do(lambda: db.session.get(Event, ev)) is None


# ---- admin -------------------------------------------------------------------------------------

def test_admin_routes_are_hidden_from_normal_users(client, make):
    make.user("owner@example.com")
    headers = api_login(client, "owner@example.com")
    assert client.get(f"{API}/admin/overview", headers=headers).status_code == 404
    assert client.get(f"{API}/admin/overview").status_code == 401


def test_admin_queue_approve_and_reject(client, make, db_do):
    org = make.org(make.user("owner@example.com"))
    a = make.event(org, title="Gut", status=Status.PENDING)
    b = make.event(org, title="Schlecht", status=Status.PENDING)
    make.user("admin@example.com", role=Role.ADMIN)
    headers = api_login(client, "admin@example.com")

    queue = client.get(f"{API}/admin/queue?kind=event", headers=headers).get_json()
    assert queue["counts"]["event"] == 2 and {i["title"] for i in queue["items"]} == {"Gut", "Schlecht"}
    assert client.get(f"{API}/auth/me", headers=headers).get_json()["pending"] == 2

    assert client.post(f"{API}/admin/event/{a}/approve", headers=headers).status_code == 200
    assert client.post(f"{API}/admin/event/{b}/reject", headers=headers, json={"reason": ""}).status_code == 422
    r = client.post(f"{API}/admin/event/{b}/reject", headers=headers, json={"reason": "Bitte Bild ändern"})
    assert r.status_code == 200
    assert db_do(lambda: (db.session.get(Event, a).status, db.session.get(Event, b).status)) == \
        (Status.APPROVED, Status.REJECTED)
    assert "Bitte Bild ändern" in mail.outbox[-1].get_body().get_content()
    assert client.get(f"{API}/admin/log", headers=headers).get_json()["total"] >= 2


def test_admin_feature_premium_and_overview(client, make, db_do):
    org = make.org(make.user("owner@example.com"))
    ev = make.event(org)
    make.user("admin@example.com", role=Role.ADMIN)
    headers = api_login(client, "admin@example.com")
    assert client.post(f"{API}/admin/event/{ev}/feature", headers=headers).get_json()["is_featured"] is True
    r = client.post(f"{API}/admin/organization/{org}/premium", headers=headers, json={"until": ""})
    assert r.status_code == 200 and r.get_json()["is_premium"] is True
    overview = client.get(f"{API}/admin/overview", headers=headers).get_json()
    assert "stats" in overview and "pending" in overview


def test_admin_block_logs_user_out_of_app(client, make):
    user_id = make.user("owner@example.com")
    user_headers = api_login(client, "owner@example.com")
    admin_id = make.user("admin@example.com", role=Role.ADMIN)
    headers = api_login(client, "admin@example.com")
    assert client.post(f"{API}/admin/users/{admin_id}/block", headers=headers).status_code == 400  # not yourself
    assert client.post(f"{API}/admin/users/{user_id}/block", headers=headers).get_json()["is_blocked"] is True
    assert client.get(f"{API}/auth/me", headers=user_headers).status_code == 401


def test_admin_categories_crud(client, make):
    make.user("admin@example.com", role=Role.ADMIN)
    headers = api_login(client, "admin@example.com")
    icons = client.get(f"{API}/admin/categories", headers=headers).get_json()["icons"]
    r = client.post(f"{API}/admin/categories", headers=headers,
                    json={"name": "Lesungen", "icon": icons[0], "color": "#8a7a5c", "sort_order": 9})
    assert r.status_code == 201, r.get_json()
    cat_id = r.get_json()["item"]["id"]
    dup = client.post(f"{API}/admin/categories", headers=headers,
                      json={"name": "Lesungen", "icon": icons[0], "color": "#8a7a5c"})
    assert dup.status_code == 422
    assert client.delete(f"{API}/admin/categories/{cat_id}", headers=headers).status_code == 200
