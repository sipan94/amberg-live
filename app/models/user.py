from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from flask_login import UserMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from ..extensions import db, login_manager
from .base import TimestampMixin

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash("timing-equalizer-not-a-real-password")


class Role:
    ORG = "org"      # business or club account
    ADMIN = "admin"
    ALL = (ORG, ADMIN)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.ORG, index=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[datetime | None]
    is_blocked: Mapped[bool] = mapped_column(default=False)
    last_login_at: Mapped[datetime | None]

    organizations: Mapped[list["Organization"]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )
    api_tokens: Mapped[list["ApiToken"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )

    @validates("email")
    def _normalize_email(self, _key, value: str) -> str:
        return (value or "").strip().lower()

    def set_password(self, password: str) -> None:
        self.password_hash = _hasher.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            _hasher.verify(self.password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
        # Upgrade old hashes transparently when Argon2 parameters change.
        if _hasher.check_needs_rehash(self.password_hash):
            self.set_password(password)
        return True

    @staticmethod
    def spend_hash_time(password: str) -> None:
        """Burn the same CPU time as a real check, for logins with unknown e-mails.
        Otherwise response time would reveal which addresses are registered."""
        try:
            _hasher.verify(_DUMMY_HASH, password)
        except VerificationError:
            pass

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_active(self) -> bool:  # used by Flask-Login: blocked users can't log in
        return not self.is_blocked

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
