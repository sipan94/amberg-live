from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from ..utils.timeutils import utcnow


class ModerationAction:
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    FEATURE = "feature"
    UNFEATURE = "unfeature"
    PREMIUM_ON = "premium_on"
    PREMIUM_OFF = "premium_off"
    BLOCK = "block"
    UNBLOCK = "unblock"
    DELETE = "delete"


_TARGET_TYPES = {
    "events": "event", "offers": "offer", "organizations": "organization", "users": "user",
}


class ModerationLog(db.Model):
    """Audit trail: who did what to which item, and why."""

    __tablename__ = "moderation_logs"
    __table_args__ = (Index("ix_moderation_logs_target", "target_type", "target_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    target_type: Mapped[str] = mapped_column(String(20))  # "event", "offer", "organization", "user"
    target_id: Mapped[int]
    target_label: Mapped[str] = mapped_column(String(200))  # kept readable after deletion
    action: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)

    admin: Mapped["User | None"] = relationship()  # noqa: F821

    @classmethod
    def record(cls, admin, target, action: str, reason: str | None = None) -> "ModerationLog":
        entry = cls(
            admin=admin,
            target_type=_TARGET_TYPES[target.__tablename__],
            target_id=target.id,
            target_label=str(getattr(target, "title", None) or getattr(target, "name", None)
                             or getattr(target, "email", ""))[:200],
            action=action,
            reason=reason,
        )
        db.session.add(entry)
        return entry
