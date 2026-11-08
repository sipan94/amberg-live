from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import ModeratedMixin, TimestampMixin


class Offer(TimestampMixin, ModeratedMixin, db.Model):
    """A deal or special from a local business (e.g. 'Mittagstisch ab 9,90 €')."""

    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)  # sanitized HTML

    valid_from: Mapped[date] = mapped_column(index=True)
    valid_until: Mapped[date | None] = mapped_column(index=True)  # None = until further notice

    image: Mapped[str | None] = mapped_column(String(255))
    rights_confirmed: Mapped[bool] = mapped_column(default=False)
    is_featured: Mapped[bool] = mapped_column(default=False, index=True)
    view_count: Mapped[int] = mapped_column(default=0)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    organization: Mapped["Organization"] = relationship(back_populates="offers")  # noqa: F821

    def slug_source(self) -> str:
        return self.title

    def is_valid_on(self, day: date) -> bool:
        return self.valid_from <= day and (self.valid_until is None or day <= self.valid_until)

    @property
    def is_public(self) -> bool:
        return self.is_approved and self.organization.is_public

    def __repr__(self) -> str:
        return f"<Offer {self.slug}>"
