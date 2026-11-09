"""Login tokens for the mobile app (Authorization: Bearer <token>).

Only a SHA-256 hash is stored: a database leak does not reveal usable tokens.
"""
import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import ForeignKey, String, delete, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from ..utils.timeutils import utcnow

TOKEN_LIFETIME = timedelta(days=90)
TOUCH_INTERVAL = timedelta(hours=1)  # don't write "last used" on every request


def _hash(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


class ApiToken(db.Model):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_used_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime]

    user: Mapped["User"] = relationship(back_populates="api_tokens")  # noqa: F821

    @classmethod
    def issue(cls, user, device: str | None = None) -> tuple[str, "ApiToken"]:
        """Create a token. The plain value is returned once and never stored."""
        plain = secrets.token_urlsafe(32)
        token = cls(user=user, token_hash=_hash(plain), device=(device or "")[:100] or None,
                    expires_at=utcnow() + TOKEN_LIFETIME)
        db.session.add(token)
        return plain, token

    @classmethod
    def find(cls, plain: str) -> "ApiToken | None":
        if not plain or len(plain) > 200:
            return None
        token = db.session.scalar(select(cls).where(cls.token_hash == _hash(plain)))
        if token is None or token.expires_at < utcnow():
            return None
        return token

    def touch(self) -> None:
        now = utcnow()
        if now - self.last_used_at > TOUCH_INTERVAL:
            self.last_used_at = now
            db.session.commit()

    @classmethod
    def revoke_all(cls, user_id: int, except_id: int | None = None) -> None:
        """Log out every device, e.g. after a password change. Caller commits."""
        stmt = delete(cls).where(cls.user_id == user_id)
        if except_id is not None:
            stmt = stmt.where(cls.id != except_id)
        db.session.execute(stmt)
