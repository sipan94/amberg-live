"""Premium listings – the single place where "is this organization premium?" changes.

Today an admin switches premium on/off. Later, Stripe subscriptions plug in here:
  - checkout success / `customer.subscription.updated` webhook -> set_premium(org, until=period_end)
  - `customer.subscription.deleted` webhook                    -> clear_premium(org)
Add a `stripe_customer_id` column to Organization and a webhook route in this package;
nothing else in the app needs to change, because all UI reads `org.is_premium`.
"""
from datetime import datetime

from sqlalchemy import select

from ..extensions import db
from ..models import ModerationAction, ModerationLog, Organization
from ..utils.timeutils import now_local


def set_premium(org: Organization, until: datetime | None = None, *, admin=None, note: str | None = None) -> None:
    org.is_premium = True
    org.premium_until = until
    ModerationLog.record(admin, org, ModerationAction.PREMIUM_ON,
                         note or (f"bis {until:%d.%m.%Y}" if until else "unbefristet"))


def clear_premium(org: Organization, *, admin=None, note: str | None = None) -> None:
    org.is_premium = False
    org.premium_until = None
    ModerationLog.record(admin, org, ModerationAction.PREMIUM_OFF, note)


def expire_premiums(now: datetime | None = None) -> int:
    """Switch off premium whose end date has passed. Run daily (cron: `flask premium-expire`)."""
    now = now or now_local()
    expired = db.session.scalars(select(Organization).where(
        Organization.is_premium.is_(True), Organization.premium_until.is_not(None),
        Organization.premium_until < now)).all()
    for org in expired:
        clear_premium(org, note="automatisch abgelaufen")
    db.session.commit()
    return len(expired)
