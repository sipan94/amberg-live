"""Shared fixtures.

Important: requests are made OUTSIDE an app context. If a test kept one app context
pushed while calling the test client, Flask would reuse it for every request and
Flask-Login would remember the previous user in `g` – tests would then pass or fail
for the wrong reasons. Database work happens in short `with app.app_context()` blocks
(see the `db_do` fixture).
"""
import io
from datetime import timedelta

import pytest
from PIL import Image

from app import create_app
from app.extensions import db
from app.models import Event, Offer, Organization, Role, Status, User
from app.seed import seed_categories
from app.services import mail
from app.utils.timeutils import now_local

PASSWORD = "test-passwort-123"
BROWSER = {"User-Agent": "Mozilla/5.0 (pytest)"}


@pytest.fixture
def app(tmp_path):
    app = create_app("testing")
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    with app.app_context():
        db.create_all()
        seed_categories()
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def _clear_outbox():
    mail.outbox.clear()
    yield
    mail.outbox.clear()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_do(app):
    """Run a function inside an app context and return its result: db_do(lambda: ...)."""
    def run(fn):
        with app.app_context():
            return fn()
    return run


class Factory:
    """Creates test data and returns plain ids (objects would be detached outside the context)."""

    def __init__(self, app):
        self.app = app

    def user(self, email="owner@example.com", role=Role.ORG, verified=True, blocked=False) -> int:
        with self.app.app_context():
            user = User(email=email, role=role, is_verified=verified, is_blocked=blocked)
            user.set_password(PASSWORD)
            db.session.add(user)
            db.session.commit()
            return user.id

    def org(self, owner_id, name="Testladen", status=Status.APPROVED, premium=False, **kw) -> int:
        with self.app.app_context():
            org = Organization(name=name, owner_id=owner_id, status=status, is_premium=premium,
                               description="<p>Beschreibung</p>", **kw)
            db.session.add(org)
            db.session.commit()
            return org.id

    def event(self, org_id, title="Testkonzert", status=Status.APPROVED, days=2, hours=2,
              recurrence="none", category_id=1, **kw) -> int:
        with self.app.app_context():
            start = (now_local() + timedelta(days=days)).replace(hour=19, minute=0, second=0)
            ev = Event(title=title, organization_id=org_id, status=status, start_at=start,
                       end_at=start + timedelta(hours=hours) if hours else None,
                       recurrence=recurrence, category_id=category_id, location_name="Saal",
                       description="<p>Live</p>", rights_confirmed=True, **kw)
            db.session.add(ev)
            db.session.commit()
            return ev.id

    def offer(self, org_id, title="10 % auf alles", status=Status.APPROVED, days_from=0, days_until=7) -> int:
        with self.app.app_context():
            today = now_local().date()
            offer = Offer(title=title, organization_id=org_id, status=status,
                          valid_from=today + timedelta(days=days_from),
                          valid_until=today + timedelta(days=days_until) if days_until is not None else None,
                          description="<p>Angebot</p>")
            db.session.add(offer)
            db.session.commit()
            return offer.id


@pytest.fixture
def make(app):
    return Factory(app)


def login(client, email, password=PASSWORD):
    return client.post("/anmelden", data={"email": email, "password": password}, headers=BROWSER)


@pytest.fixture
def owner(app, make, client):
    """A verified business owner with an approved profile, logged in on `client`."""
    user_id = make.user("owner@example.com")
    org_id = make.org(user_id)
    login(client, "owner@example.com")
    return {"user": user_id, "org": org_id}


@pytest.fixture
def admin_client(app, make):
    make.user("admin@example.com", role=Role.ADMIN)
    c = app.test_client()
    login(c, "admin@example.com")
    return c


def image_bytes(fmt="JPEG", size=(1200, 800), gps=True) -> io.BytesIO:
    img = Image.new("RGB", size, (200, 120, 40))
    buf = io.BytesIO()
    if gps:
        exif = Image.Exif()
        exif[0x8825] = {2: (49.0, 26.0, 40.0)}  # GPS latitude
        exif[0x0110] = "Secret Phone"
        img.save(buf, fmt, exif=exif.tobytes())
    else:
        img.save(buf, fmt)
    buf.seek(0)
    return buf
