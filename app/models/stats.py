from datetime import date

from sqlalchemy import String, UniqueConstraint, update
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class DailyStat(db.Model):
    """Privacy-friendly analytics: one anonymous counter per key and day. No IPs, no cookies."""

    __tablename__ = "daily_stats"
    __table_args__ = (UniqueConstraint("day", "key", name="uq_daily_stats_day_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(index=True)
    key: Mapped[str] = mapped_column(String(120))  # e.g. "page:home", "event:42"
    count: Mapped[int] = mapped_column(default=0)

    @classmethod
    def bump(cls, key: str, day: date) -> None:
        """Increment a counter (update first, insert if it didn't exist). Caller commits."""
        result = db.session.execute(
            update(cls).where(cls.day == day, cls.key == key).values(count=cls.count + 1)
        )
        if result.rowcount == 0:
            db.session.add(cls(day=day, key=key, count=1))
