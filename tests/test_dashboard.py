"""Business dashboard: permissions, submissions, re-approval rule, image uploads, account deletion."""
import io
from datetime import timedelta
from pathlib import Path

from PIL import Image

from app.extensions import db
from app.models import Event, Organization, Status, User
from app.services import mail
from app.utils.timeutils import now_local
from conftest import BROWSER, image_bytes, login


def event_form(**overrides):
    tomorrow = (now_local() + timedelta(days=1)).date().isoformat()
    data = {"title": "Sommerkonzert", "category_id": 1, "description": "Live-Musik", "start_date": tomorrow,
            "start_time": "19:00", "recurrence": "none", "location_name": "Saal", "is_free": "y",
            "rights_confirmed": "y"}
    data.update(overrides)
    return data


def test_dashboard_requires_login(client):
    r = client.get("/konto/")
    assert r.status_code == 302 and "/anmelden" in r.location


def test_unverified_user_cannot_submit(client, make):
    make.user("u@example.com", verified=False)
    login(client, "u@example.com")
    assert client.get("/konto/profil").status_code == 302
    assert client.post("/konto/veranstaltungen/neu", data=event_form()).status_code == 302


def test_create_event_goes_to_review_and_notifies_admin(client, owner, db_do):
    r = client.post("/konto/veranstaltungen/neu", data=event_form(), headers=BROWSER)
    assert r.status_code == 302
    ev = db_do(lambda: db.session.query(Event).filter_by(title="Sommerkonzert").one())
    assert ev.status == Status.PENDING and ev.organization_id == owner["org"]
    assert "Neu: Veranstaltung" in mail.outbox[-1]["Subject"]


def test_event_validation(client, owner):
    tomorrow = (now_local() + timedelta(days=1)).date().isoformat()
    body = client.post("/konto/veranstaltungen/neu",
                       data=event_form(end_date=tomorrow, end_time="18:00")).get_data(as_text=True)
    assert "nach dem Beginn" in body
    body = client.post("/konto/veranstaltungen/neu", data=event_form(start_date="2020-01-01")).get_data(as_text=True)
    assert "Vergangenheit" in body
    body = client.post("/konto/veranstaltungen/neu", data=event_form(rights_confirmed="")).get_data(as_text=True)
    assert "Rechte" in body


def test_users_cannot_touch_foreign_content(client, owner, make):
    foreign_org = make.org(make.user("fremd@example.com"), name="Fremd")
    foreign_event = make.event(foreign_org)
    assert client.get(f"/konto/veranstaltungen/{foreign_event}").status_code == 404
    assert client.post(f"/konto/veranstaltungen/{foreign_event}/loeschen").status_code == 404


def test_reapproval_rule(client, owner, make, db_do):
    eid = make.event(owner["org"], title="Sommerkonzert")
    start = db_do(lambda: db.session.get(Event, eid).start_at)
    # Same title/description as stored ("<p>Live</p>"), so only the time differs.
    base = event_form(start_date=start.date().isoformat(), start_time="19:00", description="Live")

    client.post(f"/konto/veranstaltungen/{eid}", data={**base, "start_time": "20:00"})
    assert db_do(lambda: db.session.get(Event, eid).status) == Status.APPROVED  # time change: stays live

    client.post(f"/konto/veranstaltungen/{eid}", data={**base, "start_time": "20:00", "title": "Neuer Titel"})
    assert db_do(lambda: db.session.get(Event, eid).status) == Status.PENDING  # text change: review again


def test_image_upload_is_converted_and_stripped(client, owner, db_do, app):
    data = event_form()
    data["image"] = (image_bytes("JPEG", size=(3000, 2000)), "urlaub.JPG")
    assert client.post("/konto/veranstaltungen/neu", data=data, content_type="multipart/form-data").status_code == 302
    path = db_do(lambda: db.session.query(Event).filter_by(title="Sommerkonzert").one().image)
    full = Path(app.config["UPLOAD_FOLDER"]) / path
    with Image.open(full) as img:
        assert img.format == "WEBP" and max(img.size) <= 1600
        assert len(img.getexif()) == 0  # no GPS, no camera model
    assert full.with_name(full.stem + "_sm.webp").exists()


def test_fake_image_is_rejected(client, owner):
    data = event_form()
    data["image"] = (io.BytesIO(b"<?php system($_GET['x']); ?>"), "bild.jpg")
    body = client.post("/konto/veranstaltungen/neu", data=data,
                       content_type="multipart/form-data").get_data(as_text=True)
    assert "kein gültiges Bild" in body


def test_profile_text_is_sanitized(client, make, db_do):
    make.user("neu@example.com")
    login(client, "neu@example.com")
    client.post("/konto/profil", data={"name": "Mein Laden", "org_type": "business", "rights_confirmed": "y",
                                       "description": "Hallo <script>alert(1)</script>Welt",
                                       "website": "example.com"})
    org = db_do(lambda: db.session.query(Organization).filter_by(name="Mein Laden").one())
    assert "<script>" not in org.description and org.website == "https://example.com"
    assert org.status == Status.PENDING


def test_account_deletion_removes_everything(client, owner, db_do, app):
    data = event_form()
    data["image"] = (image_bytes(), "a.jpg")
    client.post("/konto/veranstaltungen/neu", data=data, content_type="multipart/form-data")
    uploads = Path(app.config["UPLOAD_FOLDER"])
    assert list(uploads.rglob("*.webp"))

    r = client.post("/konto/loeschen", data={"password": "falsch", "confirm": "y"})
    assert "nicht korrekt" in r.get_data(as_text=True)
    r = client.post("/konto/loeschen", data={"password": "test-passwort-123", "confirm": "y"})
    assert r.status_code == 302
    assert db_do(lambda: db.session.get(User, owner["user"])) is None
    assert db_do(lambda: db.session.query(Event).count()) == 0
    assert list(uploads.rglob("*.webp")) == []
