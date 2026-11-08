"""Admin area: access, moderation, featured/premium, users, categories."""
from datetime import timedelta

from sqlalchemy import select

from app.billing import expire_premiums
from app.extensions import db
from app.models import Category, Event, ModerationLog, Organization, Role, Status, User
from app.services import mail
from app.utils.timeutils import now_local
from conftest import BROWSER, login


def test_admin_area_hidden_from_others(client, owner):
    assert client.get("/admin/").status_code == 404


def test_admin_pages_load(admin_client, make):
    org = make.org(make.user())
    eid = make.event(org)
    for url in ["/admin/", "/admin/pruefung", "/admin/inhalte/veranstaltung", "/admin/inhalte/profil",
                "/admin/nutzer", "/admin/kategorien", "/admin/protokoll", f"/admin/veranstaltung/{eid}/bearbeiten"]:
        assert admin_client.get(url).status_code == 200, url


def test_approve_sends_mail_and_logs(admin_client, make, db_do):
    eid = make.event(make.org(make.user()), status=Status.PENDING)
    admin_client.post(f"/admin/veranstaltung/{eid}/freigeben")
    assert db_do(lambda: db.session.get(Event, eid).status) == Status.APPROVED
    assert mail.outbox[-1]["To"] == "owner@example.com" and "online" in mail.outbox[-1]["Subject"]
    assert db_do(lambda: db.session.scalar(select(ModerationLog.action))) == "approve"


def test_reject_requires_reason_and_tells_owner(admin_client, make, db_do):
    eid = make.event(make.org(make.user()), status=Status.PENDING)
    admin_client.post(f"/admin/veranstaltung/{eid}/ablehnen", data={"reason": ""})
    assert db_do(lambda: db.session.get(Event, eid).status) == Status.PENDING

    admin_client.post(f"/admin/veranstaltung/{eid}/ablehnen", data={"reason": "Bitte Uhrzeit ergänzen."})
    ev = db_do(lambda: db.session.get(Event, eid))
    assert ev.status == Status.REJECTED and ev.rejection_reason == "Bitte Uhrzeit ergänzen."
    assert "Uhrzeit ergänzen" in mail.outbox[-1].get_content()


def test_rejected_event_goes_back_to_review_after_edit(client, owner, make, db_do):
    eid = make.event(owner["org"], status=Status.REJECTED)
    start = db_do(lambda: db.session.get(Event, eid).start_at)
    client.post(f"/konto/veranstaltungen/{eid}", data={
        "title": "Testkonzert", "category_id": 1, "description": "Jetzt mit Uhrzeit",
        "start_date": start.date().isoformat(), "start_time": "19:00", "recurrence": "none",
        "location_name": "Saal", "is_free": "y", "rights_confirmed": "y"})
    assert db_do(lambda: db.session.get(Event, eid).status) == Status.PENDING


def test_featured_and_premium(admin_client, make, db_do, client):
    org = make.org(make.user())
    eid = make.event(org)
    admin_client.post(f"/admin/veranstaltung/{eid}/hervorheben")
    assert db_do(lambda: db.session.get(Event, eid).is_featured)

    until = (now_local() + timedelta(days=30)).date().isoformat()
    admin_client.post(f"/admin/profil/{org}/premium", data={"until": until})
    assert db_do(lambda: db.session.get(Organization, org).is_premium)
    assert "Partner" in client.get("/geschaefte-vereine", headers=BROWSER).get_data(as_text=True)

    assert db_do(lambda: expire_premiums(now_local() + timedelta(days=31))) == 1
    assert not db_do(lambda: db.session.get(Organization, org).is_premium)


def test_admin_edit_keeps_status(admin_client, make, db_do):
    eid = make.event(make.org(make.user()))
    start = db_do(lambda: db.session.get(Event, eid).start_at)
    admin_client.post(f"/admin/veranstaltung/{eid}/bearbeiten", data={
        "title": "Korrigierter Titel", "category_id": 1, "description": "x",
        "start_date": start.date().isoformat(), "start_time": "19:00", "recurrence": "none",
        "location_name": "Saal", "is_free": "y", "rights_confirmed": "y"})
    ev = db_do(lambda: db.session.get(Event, eid))
    assert ev.title == "Korrigierter Titel" and ev.status == Status.APPROVED


def test_block_user_hides_content_and_prevents_login(admin_client, make, db_do, app):
    uid = make.user("sperren@example.com")
    eid = make.event(make.org(uid))
    slug = db_do(lambda: db.session.get(Event, eid).slug)
    admin_client.post(f"/admin/nutzer/{uid}/sperren")
    visitor = app.test_client()
    assert visitor.get(f"/veranstaltungen/{slug}", headers=BROWSER).status_code == 404
    assert login(app.test_client(), "sperren@example.com").status_code == 403


def test_admin_cannot_block_or_delete_self(admin_client, db_do):
    me = db_do(lambda: db.session.scalar(select(User.id).where(User.role == Role.ADMIN)))
    assert admin_client.post(f"/admin/nutzer/{me}/sperren").status_code == 400
    assert admin_client.post(f"/admin/nutzer/{me}/loeschen").status_code == 400


def test_delete_user_anonymizes_log(admin_client, make, db_do):
    uid = make.user("weg@example.com")
    admin_client.post(f"/admin/nutzer/{uid}/sperren")
    admin_client.post(f"/admin/nutzer/{uid}/loeschen")
    assert db_do(lambda: db.session.get(User, uid)) is None
    labels = db_do(lambda: db.session.scalars(select(ModerationLog.target_label)).all())
    assert labels and all("weg@example.com" not in label for label in labels)


def test_category_management(admin_client, db_do):
    admin_client.post("/admin/kategorien/neu", data={"name": "Kino", "icon": "star", "color": "#123456"})
    assert db_do(lambda: db.session.scalar(select(Category.slug).where(Category.name == "Kino"))) == "kino"
    body = admin_client.post("/admin/kategorien/neu",
                             data={"name": "Kino", "icon": "star", "color": "#123456"}).get_data(as_text=True)
    assert "gibt es schon" in body
