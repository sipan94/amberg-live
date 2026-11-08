"""HTML sanitizing for user-written descriptions (bleach)."""
import html
import re
from functools import lru_cache

import bleach
from bleach.callbacks import nofollow

ALLOWED_TAGS = ["p", "br", "strong", "b", "em", "i", "ul", "ol", "li", "a", "h3", "h4", "blockquote"]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]


def _external(attrs, new=False):
    attrs[(None, "target")] = "_blank"
    rel = set(attrs.get((None, "rel"), "").split())
    attrs[(None, "rel")] = " ".join(sorted(rel | {"noopener", "noreferrer", "nofollow"}))
    return attrs


@lru_cache(maxsize=1024)
def sanitize_html(value: str | None) -> str:
    """Keep simple formatting, drop everything else (scripts, styles, event handlers)."""
    cleaned = bleach.clean(value or "", tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES,
                           protocols=ALLOWED_PROTOCOLS, strip=True)
    return bleach.linkify(cleaned, callbacks=[nofollow, _external], parse_email=False)


def text_to_html(text: str | None) -> str:
    """Form textarea -> stored HTML. Blank lines start paragraphs, single newlines become <br>.
    Simple tags like <b> or <a> typed by the user survive; everything else is removed."""
    text = (text or "").replace("\r\n", "\n").strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return sanitize_html("".join("<p>" + p.replace("\n", "<br>") + "</p>" for p in paragraphs))


def html_to_text(value: str | None) -> str:
    """Stored HTML -> textarea content for editing (inverse of text_to_html)."""
    text = re.sub(r"<br\s*/?>", "\n", value or "")
    text = re.sub(r"</p>\s*", "\n\n", text)
    # Remove <p> ourselves: bleach adds an extra newline when it strips block tags,
    # which would grow the text by one blank line on every edit.
    text = re.sub(r"<p[^>]*>", "", text)
    text = bleach.clean(text, tags=["b", "strong", "i", "em"], strip=True)
    return html.unescape(text).strip()


def to_plain_text(value: str | None, limit: int | None = None) -> str:
    """Strip all tags, e.g. for meta descriptions and .ics files."""
    text = bleach.clean(re.sub(r"</p>|<br\s*/?>", " ", value or ""), tags=[], strip=True)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if limit and len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0] + "…"
    return text
