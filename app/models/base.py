"""Shared column sets used by several models."""
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..utils.timeutils import utcnow


class Status:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ALL = (PENDING, APPROVED, REJECTED)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)


class ModeratedMixin:
    """Content that an admin must approve before it is public."""

    status: Mapped[str] = mapped_column(String(20), default=Status.PENDING, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500))
    reviewed_at: Mapped[datetime | None]

    @property
    def is_approved(self) -> bool:
        return self.status == Status.APPROVED

    @property
    def is_pending(self) -> bool:
        return self.status == Status.PENDING

    @property
    def is_rejected(self) -> bool:
        return self.status == Status.REJECTED
