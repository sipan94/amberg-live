from datetime import date, datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from ..utils import recurrence
from .base import ModeratedMixin, TimestampMixin


class Event(TimestampMixin, ModeratedMixin, db.Model):
    __tablename__ = "events"
    __table_args__ = (Index("ix_events_status_start", "status", "start_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)  # sanitized HTML

    # Local Amberg time (see utils/timeutils.py). For recurring events: the first occurrence.
    start_at: Mapped[datetime] = mapped_column(index=True)
    end_at: Mapped[datetime | None]
    recurrence: Mapped[str] = mapped_column(String(10), default=recurrence.NONE)
    recurrence_until: Mapped[date | None]  # last day a recurring event can happen

    location_name: Mapped[str | None] = mapped_column(String(150))
    address: Mapped[str | None] = mapped_column(String(255))
    lat: Mapped[float | None]
    lng: Mapped[float | None]

    is_free: Mapped[bool] = mapped_column(default=True)
    price_info: Mapped[str | None] = mapped_column(String(100))  # e.g. "VVK 12 €, AK 15 €"

    image: Mapped[str | None] = mapped_column(String(255))
    rights_confirmed: Mapped[bool] = mapped_column(default=False)
    is_featured: Mapped[bool] = mapped_column(default=False, index=True)
    view_count: Mapped[int] = mapped_column(default=0)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )

    category: Mapped["Category | None"] = relationship(back_populates="events")  # noqa: F821
    organization: Mapped["Organization"] = relationship(back_populates="events")  # noqa: F821

    def slug_source(self) -> str:
        # Date in the slug keeps yearly events (e.g. Christkindlmarkt) apart and helps SEO.
        return f"{self.title} {self.start_at:%Y-%m-%d}" if self.start_at else self.title

    @property
    def is_recurring(self) -> bool:
        return self.recurrence in (recurrence.WEEKLY, recurrence.MONTHLY)

    @property
    def is_public(self) -> bool:
        return self.is_approved and self.organization.is_public

    def occurrences_between(self, window_start: datetime, window_end: datetime):
        """List of (start, end) for every occurrence overlapping the window."""
        return list(recurrence.iter_occurrences(
            self.start_at, self.end_at, self.recurrence, self.recurrence_until,
            window_start, window_end,
        ))

    def __repr__(self) -> str:
        return f"<Event {self.slug}>"
