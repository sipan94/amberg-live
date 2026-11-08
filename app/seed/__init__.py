"""Seed logic used by `flask seed` and `flask seed-categories`."""
from datetime import timedelta

from flask import current_app
from sqlalchemy import func, select

from ..extensions import db
from ..models import (Category, Event, ModerationAction, ModerationLog, Offer, Organization,
                      Role, Status, User)
from ..utils.timeutils import today_local, utcnow
from .categories import CATEGORIES
from .demo_data import ORGANIZATIONS, build_events, build_offers


class SeedError(Exception):
    pass


def seed_categories() -> dict[str, Category]:
    """Insert or update the default categories (idempotent)."""
    by_slug = {c.slug: c for c in db.session.scalars(select(Category))}
    for order, (name, slug, icon, color) in enumerate(CATEGORIES):
        cat = by_slug.get(slug) or Category(slug=slug)
        cat.name, cat.icon, cat.color, cat.sort_order = name, icon, color, order
        db.session.add(cat)
        by_slug[slug] = cat
    db.session.flush()
    return by_slug


def _wipe_all_data() -> None:
    # Children first, so foreign keys never point to deleted rows.
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.flush()


def run_seed(password: str, reset: bool = False) -> dict:
    if reset:
        _wipe_all_data()
    elif db.session.scalar(select(func.count(User.id))):
        raise SeedError("The database already has users. Run `flask seed --reset` to start over.")

    now = utcnow()
    today = today_local()
    categories = seed_categories()

    admin = User(email=current_app.config["ADMIN_EMAIL"], role=Role.ADMIN,
                 is_verified=True, verified_at=now)
    admin.set_password(password)
    db.session.add(admin)

    orgs: dict[str, Organization] = {}
    for data in ORGANIZATIONS:
        if data["owner"] == "ADMIN":
            owner = admin
        else:
            owner = User(email=data["owner"], role=Role.ORG, is_verified=True, verified_at=now)
            owner.set_password(password)
            db.session.add(owner)
        org = Organization(
            name=data["name"], org_type=data["type"], description=data["description"],
            address=data["address"], lat=data["lat"], lng=data["lng"], phone=data["phone"],
            email=data["email"], website=data["website"], opening_hours=data["hours"],
            is_premium=data["premium"], status=data["status"], owner=owner,
            reviewed_at=now if data["status"] != Status.PENDING else None,
        )
        db.session.add(org)
        orgs[data["key"]] = org

    events = []
    for data in build_events(today):
        name, address, lat, lng = data["venue"]
        start = data["start"]
        end = data.get("end") or (start + timedelta(hours=data["dur_h"]) if "dur_h" in data else None)
        status = data.get("status", Status.APPROVED)
        event = Event(
            title=data["title"], description=data["desc"], start_at=start, end_at=end,
            recurrence=data.get("recurrence", "none"), location_name=name, address=address,
            lat=lat, lng=lng, is_free=data.get("free", True), price_info=data.get("price"),
            category=categories[data["cat"]], organization=orgs[data["org"]],
            status=status, rejection_reason=data.get("reason"),
            is_featured=data.get("featured", False), rights_confirmed=True,
            reviewed_at=now if status != Status.PENDING else None,
            view_count=0 if status != Status.APPROVED else 20 + len(events) * 7,
        )
        db.session.add(event)
        events.append(event)

    offers = []
    for data in build_offers(today):
        status = data.get("status", Status.APPROVED)
        offer = Offer(
            title=data["title"], description=data["desc"], valid_from=data["valid_from"],
            valid_until=data["valid_until"], organization=orgs[data["org"]], status=status,
            is_featured=data.get("featured", False), rights_confirmed=True,
            reviewed_at=now if status != Status.PENDING else None,
        )
        db.session.add(offer)
        offers.append(offer)

    db.session.flush()  # assigns ids and slugs

    for item in [*orgs.values(), *events, *offers]:
        if item.status == Status.APPROVED:
            ModerationLog.record(admin, item, ModerationAction.APPROVE)
        elif item.status == Status.REJECTED:
            ModerationLog.record(admin, item, ModerationAction.REJECT, item.rejection_reason)

    db.session.commit()

    return {
        "admin_email": admin.email,
        "sample_org_email": orgs["cafe"].owner.email,
        "counts": {
            "categories": len(categories),
            "users": db.session.scalar(select(func.count(User.id))),
            "organizations": len(orgs),
            "events": len(events),
            "offers": len(offers),
        },
    }
