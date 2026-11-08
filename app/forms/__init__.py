"""Shared form helpers."""
from wtforms.validators import Length

from ..i18n import t


class LazyText:
    """Translation looked up when displayed, not when the form class is defined.
    Lets validator messages live in de.json (and later en.json)."""

    def __init__(self, key: str):
        self.key = key

    def __str__(self) -> str:
        return t(self.key)

    def __mod__(self, values) -> str:  # WTForms formats messages with "%"
        return str(self) % values

    def __html__(self) -> str:
        return str(self)


def _l(key: str) -> LazyText:
    return LazyText(f"validation.{key}")


def max_len(n: int) -> Length:
    return Length(max=n, message=_l("too_long"))


def strip(value):
    return value.strip() if isinstance(value, str) else value


def normalize_url(value):
    value = strip(value)
    if value and not value.lower().startswith(("http://", "https://")):
        value = "https://" + value
    return value
