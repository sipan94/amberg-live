"""Finding public events and expanding them into dated occurrences."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import Category, Event, Organization, Status, User
from ..utils import recurrence


@dataclass(frozen=True)
class Occurrence:
    """One concrete date of an event (recurring events have many)."""

    event: Event
    start: datetime
    end: datetime | None

    @property
    def is_highlight(self) -> bool:
        return self.event.is_featured or self.event.organization.is_premium

    def is_ongoing(self, now: datetime) -> bool:
        return self.start <= now and self.end is not None and now < self.end


@dataclass
class EventFilter:
    start: datetime
    end: datetime
    category: str | None = None
    price: str | None = None          # "kostenlos" | "kostenpflichtig"
    q: str | None = None
    organization_id: int | None = None


def public_events() -> Select:
    """Approved events of approved organizations whose owner isn't blocked."""
    return (
        select(Event)
        .join(Event.organization)
        .join(Organization.owner)
        .where(Event.status == Status.APPROVED,
               Organization.status == Status.APPROVED,
               User.is_blocked.is_(False))
        .options(selectinload(Event.category), selectinload(Event.organization))
    )


def find_occurrences(f: EventFilter) -> list[Occurrence]:
    """All occurrences overlapping the filter window, sorted by start time."""
    single = and_(Event.recurrence == recurrence.NONE,
                  func.coalesce(Event.end_at, Event.start_at) >= f.start)
    repeating = and_(Event.recurrence != recurrence.NONE,
                     or_(Event.recurrence_until.is_(None), Event.recurrence_until >= f.start.date()))
    stmt = public_events().where(Event.start_at < f.end, or_(single, repeating))

    if f.category:
        stmt = stmt.join(Event.category).where(Category.slug == f.category)
    if f.price == "kostenlos":
        stmt = stmt.where(Event.is_free.is_(True))
    elif f.price == "kostenpflichtig":
        stmt = stmt.where(Event.is_free.is_(False))
    if f.q:
        stmt = stmt.where(or_(Event.title.icontains(f.q, autoescape=True),
                              Event.description.icontains(f.q, autoescape=True),
                              Event.location_name.icontains(f.q, autoescape=True),
                              Organization.name.icontains(f.q, autoescape=True)))
    if f.organization_id:
        stmt = stmt.where(Event.organization_id == f.organization_id)

    found = [
        Occurrence(event, start, end)
        for event in db.session.scalars(stmt)
        for start, end in event.occurrences_between(f.start, f.end)
    ]
    found.sort(key=lambda o: (o.start, o.event.title))
    return found


def first_per_event(occurrences: list[Occurrence]) -> list[Occurrence]:
    """Keep only the earliest occurrence of each event (e.g. one 'Wochenmarkt', not four)."""
    seen: set[int] = set()
    result = []
    for occ in occurrences:
        if occ.event.id not in seen:
            seen.add(occ.event.id)
            result.append(occ)
    return result


def highlight_sort_key(occ: Occurrence):
    """Ranking for the home page sections "Heute" and "Wochenende" (used with sorted()).

    Python sorts tuples element by element, and False sorts before True.
    """
    # Featured first, then premium, then start time. Adjust here if paid placement
    # should only win within a time slot (e.g. key on occ.start.hour // 6 first).
    return (not occ.event.is_featured, not occ.event.organization.is_premium, occ.start)


# ---- time windows -----------------------------------------------------------

def day_start(day: date) -> datetime:
    return datetime.combine(day, time.min)


def today_window(now: datetime) -> tuple[datetime, datetime]:
    return now, day_start(now.date() + timedelta(days=1))


def weekend_window(now: datetime) -> tuple[datetime, datetime]:
    """Friday 17:00 until Monday 00:00. During the weekend it starts now."""
    weekday = now.weekday()
    monday = day_start(now.date() + timedelta(days=7 - weekday))
    friday_evening = datetime.combine(now.date() + timedelta(days=4 - weekday), time(17))
    return max(now, friday_evening), monday


def upcoming_dates(event: Event, after: datetime, limit: int = 6) -> list[tuple[datetime, datetime | None]]:
    """Next occurrences of one event (for the detail page)."""
    horizon = after + timedelta(days=400)
    return event.occurrences_between(after, horizon)[:limit]


def last_occurrence_end(event: Event) -> datetime | None:
    """When does this event finish for good? None = open-ended series."""
    if event.is_recurring:
        if event.recurrence_until is None:
            return None
        return day_start(event.recurrence_until + timedelta(days=1))
    return event.end_at or event.start_at
