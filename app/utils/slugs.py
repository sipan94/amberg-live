"""URL slugs: German-aware, unique per table, assigned automatically on insert."""
from slugify import slugify
from sqlalchemy import event, select
from sqlalchemy.orm import Session

GERMAN_REPLACEMENTS = [
    ["ä", "ae"], ["ö", "oe"], ["ü", "ue"],
    ["Ä", "Ae"], ["Ö", "Oe"], ["Ü", "Ue"], ["ß", "ss"],
]


def make_slug(text: str, max_length: int = 80) -> str:
    slug = slugify(text or "", replacements=GERMAN_REPLACEMENTS,
                   max_length=max_length, word_boundary=True)
    return slug or "eintrag"


def unique_slug(session: Session, model, text: str, exclude_id=None, taken=frozenset()) -> str:
    base = make_slug(text)
    slug, n = base, 2
    while True:
        existing = session.scalar(select(model.id).where(model.slug == slug))
        if (existing is None or existing == exclude_id) and slug not in taken:
            return slug
        slug = f"{base}-{n}"
        n += 1


_registered = False


def register_slug_listener() -> None:
    """Give every new object with a `slug_source()` method a unique slug before it is saved."""
    global _registered
    if _registered:
        return
    _registered = True

    @event.listens_for(Session, "before_flush")
    def _assign_slugs(session, _ctx, _instances):
        taken: dict[type, set[str]] = {}
        with session.no_autoflush:
            for obj in session.new:
                if not hasattr(obj, "slug_source") or getattr(obj, "slug", None):
                    continue
                model = type(obj)
                used = taken.setdefault(model, set())
                obj.slug = unique_slug(session, model, obj.slug_source(), taken=used)
                used.add(obj.slug)
