from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import ModeratedMixin, TimestampMixin


class OrgType:
    BUSINESS = "business"
    CLUB = "club"
    ALL = (BUSINESS, CLUB)


WEEKDAYS = ("mo", "di", "mi", "do", "fr", "sa", "so")


class Organization(TimestampMixin, ModeratedMixin, db.Model):
    """A business (Geschäft) or club (Verein) with its own public profile page."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(170), unique=True, index=True)
    org_type: Mapped[str] = mapped_column("type", String(20), default=OrgType.BUSINESS, index=True)
    description: Mapped[str | None] = mapped_column(Text)  # sanitized HTML

    address: Mapped[str | None] = mapped_column(String(255))
    lat: Mapped[float | None]
    lng: Mapped[float | None]
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(254))  # public contact address
    website: Mapped[str | None] = mapped_column(String(255))
    # {"mo": "09:00–18:00", "so": "geschlossen", ...}
    opening_hours: Mapped[dict | None] = mapped_column(JSON)

    logo: Mapped[str | None] = mapped_column(String(255))
    cover_image: Mapped[str | None] = mapped_column(String(255))

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Monetization: set by admin now, by the payments module later.
    is_premium: Mapped[bool] = mapped_column(default=False, index=True)
    premium_until: Mapped[datetime | None]

    owner: Mapped["User"] = relationship(back_populates="organizations")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        back_populates="organization", cascade="all, delete-orphan"
    )
    offers: Mapped[list["Offer"]] = relationship(  # noqa: F821
        back_populates="organization", cascade="all, delete-orphan"
    )

    def slug_source(self) -> str:
        return self.name

    @property
    def is_club(self) -> bool:
        return self.org_type == OrgType.CLUB

    @property
    def is_public(self) -> bool:
        return self.is_approved and not self.owner.is_blocked

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"
