"""Signed, expiring tokens for e-mail links (no database table needed)."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

VERIFY_MAX_AGE = 60 * 60 * 24 * 3   # 3 days
RESET_MAX_AGE = 60 * 60             # 1 hour


def _serializer(purpose: str) -> URLSafeTimedSerializer:
    # A different salt per purpose: a verification token can never be used as a reset token.
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=f"amberg-live-{purpose}")


def make_verify_token(user) -> str:
    return _serializer("verify").dumps({"uid": user.id, "email": user.email})


def make_reset_token(user) -> str:
    # Part of the current password hash: once the password changes, old links stop working.
    return _serializer("reset").dumps({"uid": user.id, "ph": user.password_hash[-12:]})


def read_token(token: str, purpose: str, max_age: int) -> dict | None:
    try:
        data = _serializer(purpose).loads(token, max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    return data if isinstance(data, dict) else None
