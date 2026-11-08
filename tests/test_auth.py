"""Accounts: registration, verification, login, password reset, CSRF and rate limits."""
import re

from app import create_app
from app.extensions import db
from app.models import User
from app.services import mail
from conftest import BROWSER, PASSWORD, login


def link_from_last_mail() -> str:
    return re.search(r"https?://\S+", mail.outbox[-1].get_content()).group(0).replace("http://localhost", "")


def register(client, email="neu@example.com", password="sicheres-passwort-1"):
    return client.post("/registrieren", data={"email": email, "password": password,
                                             "password2": password, "accept_terms": "y"})


def test_register_verify_login(client, db_do):
    r = register(client)
    assert r.status_code == 302 and "fast-geschafft" in r.location
    assert not db_do(lambda: db.session.query(User).filter_by(email="neu@example.com").one().is_verified)

    assert client.get(link_from_last_mail()).status_code == 302
    assert db_do(lambda: db.session.query(User).filter_by(email="neu@example.com").one().is_verified)
    r = login(client, "neu@example.com", "sicheres-passwort-1")
    assert r.status_code == 302 and r.location.endswith("/konto/")


def test_register_validation_messages_are_german(client):
    r = client.post("/registrieren", data={"email": "kaputt", "password": "kurz", "password2": "anders"})
    body = r.get_data(as_text=True)
    assert "gültige E-Mail-Adresse" in body and "mindestens 10 Zeichen" in body and "AGB" in body


def test_duplicate_registration_does_not_reveal_account(client, make):
    make.user("vorhanden@example.com")
    r = register(client, "vorhanden@example.com")
    assert r.status_code == 302 and "fast-geschafft" in r.location  # same as a new sign-up
    assert "bereits ein Konto" in mail.outbox[-1]["Subject"]


def test_wrong_password_and_unknown_email_look_the_same(client, make):
    make.user("x@example.com")
    a = login(client, "x@example.com", "falsch-falsch").get_data(as_text=True)
    b = login(client, "niemand@example.com", "falsch-falsch").get_data(as_text=True)
    assert "E-Mail-Adresse oder Passwort ist falsch" in a and "E-Mail-Adresse oder Passwort ist falsch" in b


def test_blocked_user_cannot_login(client, make):
    make.user("gesperrt@example.com", blocked=True)
    assert login(client, "gesperrt@example.com").status_code == 403


def test_open_redirect_is_blocked(client, make):
    make.user("y@example.com")
    r = client.post("/anmelden?next=https://evil.example/phish",
                    data={"email": "y@example.com", "password": PASSWORD}, headers=BROWSER)
    assert r.location.endswith("/konto/")


def test_password_reset_link_works_once(client, make):
    make.user("reset@example.com")
    client.post("/passwort-vergessen", data={"email": "reset@example.com"})
    link = link_from_last_mail()
    r = client.post(link, data={"password": "brandneues-passwort", "password2": "brandneues-passwort"})
    assert r.status_code == 302
    assert login(client, "reset@example.com", "brandneues-passwort").status_code == 302
    assert client.get(link).status_code == 302  # old link no longer valid (redirect to "request new")


def test_forgot_password_for_unknown_email_sends_nothing(client):
    r = client.post("/passwort-vergessen", data={"email": "niemand@example.com"})
    assert r.status_code == 302 and mail.outbox == []


def test_logout_requires_post(client, owner):
    assert client.get("/abmelden").status_code == 405


def test_csrf_protection_is_active(tmp_path):
    app = create_app("testing")
    app.config.update(WTF_CSRF_ENABLED=True, UPLOAD_FOLDER=str(tmp_path))
    with app.app_context():
        db.create_all()
    r = app.test_client().post("/anmelden", data={"email": "a@example.com", "password": "x" * 12})
    assert r.status_code == 400


def test_login_rate_limit(tmp_path):
    from app.extensions import limiter

    app = create_app("testing", {"RATELIMIT_ENABLED": True, "UPLOAD_FOLDER": str(tmp_path)})
    try:
        with app.app_context():
            db.create_all()
        c = app.test_client()
        codes = [c.post("/anmelden", data={"email": "a@example.com", "password": "falsch"}).status_code
                 for _ in range(11)]
        assert codes[:10] == [200] * 10      # 10 attempts per minute are allowed
        assert codes[10] == 429               # the 11th is blocked
        blocked = c.post("/anmelden", data={"email": "a@example.com", "password": "falsch"})
        assert "Zu viele Versuche" in blocked.get_data(as_text=True)
    finally:
        limiter.reset()
        create_app("testing")  # re-initialize the shared limiter with limits disabled
