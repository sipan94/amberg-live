"""Expand recurring events (none / weekly / monthly) into concrete occurrences.

Only the first occurrence is stored in the database. Lists, the calendar and
"Heute / Wochenende" ask this module which occurrences fall into a time window.
"""
import calendar
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from itertools import count

NONE = "none"
WEEKLY = "weekly"
MONTHLY = "monthly"
RULES = (NONE, WEEKLY, MONTHLY)
# Safety net so a broken rule can never loop forever.
MAX_STEPS = 500


def add_months(start: datetime, months: int) -> datetime | None:
    """Return the occurrence `months` months after `start` (same time of day).

    Always computed from the ORIGINAL start, never chained, so a series that
    starts on the 31st doesn't drift to the 28th forever after February.
    Return None to skip a month in which the occurrence doesn't exist.
    """
    # Days that don't exist (31 Feb) move to the month's last day: 31 Jan -> 28 Feb -> 31 Mar.
    year, month_index = divmod(start.month - 1 + months, 12)
    year += start.year
    month = month_index + 1
    day = min(start.day, last_day_of_month(year, month))
    return start.replace(year=year, month=month, day=day)


def iter_occurrences(
    start: datetime,
    end: datetime | None,
    rule: str,
    until: date | None,
    window_start: datetime,
    window_end: datetime,
) -> Iterator[tuple[datetime, datetime | None]]:
    """Yield (start, end) of every occurrence that overlaps [window_start, window_end)."""
    duration = (end - start) if end else timedelta(0)

    if rule == WEEKLY:
        step = timedelta(weeks=1)
        # Jump straight to the window instead of walking from a start years ago.
        first = max(0, (window_start - duration - start) // step)
        candidates = (start + n * step for n in count(first))
    elif rule == MONTHLY:
        gap = (window_start.year - start.year) * 12 + (window_start.month - start.month) - 1
        candidates = (add_months(start, n) for n in count(max(0, gap)))
    else:
        candidates = iter([start])

    for steps, occ in enumerate(candidates):
        if steps >= MAX_STEPS:
            break
        if occ is None:  # month skipped by the monthly rule
            continue
        if occ >= window_end or (until and occ.date() > until):
            break
        occ_end = occ + duration
        if occ_end > window_start or occ >= window_start:
            yield occ, (occ_end if end else None)


def last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]
