from sqlalchemy import Select, or_, select

from ..models import Offer, Organization, Status, User
from ..utils.timeutils import today_local


def current_offers_query() -> Select:
    """Approved offers valid today, highlights first."""
    today = today_local()
    return (
        select(Offer).join(Offer.organization).join(Organization.owner)
        .where(Offer.status == Status.APPROVED, Organization.status == Status.APPROVED,
               User.is_blocked.is_(False), Offer.valid_from <= today,
               or_(Offer.valid_until.is_(None), Offer.valid_until >= today))
        .order_by(Offer.is_featured.desc(), Organization.is_premium.desc(), Offer.valid_from.desc())
    )
