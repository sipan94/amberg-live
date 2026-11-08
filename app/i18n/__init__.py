"""Tiny translation helper. All UI text lives in app/i18n/<locale>.json.

Usage in Python:   t("events.results", count=5)
Usage in Jinja:    {{ t("events.results", count=5) }}
Adding English later: create en.json with the same keys and pick the locale per request.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

from flask import current_app, has_app_context

_DIR = Path(__file__).parent
log = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def _catalog(locale: str) -> dict:
    with open(_DIR / f"{locale}.json", encoding="utf-8") as fh:
        return json.load(fh)


def current_locale() -> str:
    return current_app.config.get("DEFAULT_LOCALE", "de") if has_app_context() else "de"


def t(key: str, **params):
    """Look up a dotted key. Missing keys return the key itself, so gaps are visible."""
    node = _catalog(current_locale())
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            log.warning("Missing translation: %s", key)
            return key
        node = node[part]
    if isinstance(node, str) and params:
        return node.format(**params)
    return node
