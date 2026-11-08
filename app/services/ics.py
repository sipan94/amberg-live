"""iCalendar (.ics) export for 'Zum Kalender hinzufügen' (RFC 5545)."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from ..utils import recurrence
from ..utils.html import to_plain_text
from ..utils.timeutils import utcnow

TZID = "Europe/Berlin"
DEFAULT_DURATION = timedelta(hours=2)

# Outlook needs the timezone spelled out; Google/Apple accept it too.
VTIMEZONE = [
    "BEGIN:VTIMEZONE", f"TZID:{TZID}",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200", "TZNAME:CEST",
    "DTSTART:19700329T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET",
    "DTSTART:19701025T030000", "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD",
    "END:VTIMEZONE",
]


def _escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line: str) -> list[str]:
    """Lines longer than 75 bytes must be folded (continuation lines start with a space)."""
    out, current = [], ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            out.append(current)
            current = " " + char
        else:
            current += char
    out.append(current)
    return out


def _local(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def _rrule(event) -> str | None:
    if event.recurrence == recurrence.WEEKLY:
        rule = "FREQ=WEEKLY"
    elif event.recurrence == recurrence.MONTHLY:
        day = event.start_at.day
        # Our monthly rule moves the 29th-31st to the month's last day when it's shorter.
        # "Pick the last existing day among 28..day" expresses exactly that in RRULE.
        if day > 28:
            rule = f"FREQ=MONTHLY;BYMONTHDAY={','.join(map(str, range(28, day + 1)))};BYSETPOS=-1"
        else:
            rule = "FREQ=MONTHLY"
    else:
        return None
    if event.recurrence_until:
        # With a TZID start, UNTIL must be given in UTC.
        last = datetime.combine(event.recurrence_until, time(23, 59, 59), tzinfo=ZoneInfo(TZID))
        rule += f";UNTIL={last.astimezone(ZoneInfo('UTC')):%Y%m%dT%H%M%SZ}"
    return "RRULE:" + rule


def event_to_ics(event, url: str, host: str) -> str:
    end = event.end_at or (event.start_at + DEFAULT_DURATION)
    location = ", ".join(p for p in (event.location_name, event.address) if p)
    description = to_plain_text(event.description)
    if url:
        description = f"{description}\n\n{url}".strip()

    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Amberg Live//DE", "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH", *VTIMEZONE,
        "BEGIN:VEVENT",
        f"UID:event-{event.id}@{host}",
        f"DTSTAMP:{utcnow():%Y%m%dT%H%M%SZ}",
        f"DTSTART;TZID={TZID}:{_local(event.start_at)}",
        f"DTEND;TZID={TZID}:{_local(end)}",
        f"SUMMARY:{_escape(event.title)}",
    ]
    if rule := _rrule(event):
        lines.append(rule)
    if location:
        lines.append(f"LOCATION:{_escape(location)}")
    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")
    if url:
        lines.append(f"URL:{url}")
    if event.lat is not None and event.lng is not None:
        lines.append(f"GEO:{event.lat:.6f};{event.lng:.6f}")
    lines += ["END:VEVENT", "END:VCALENDAR"]

    return "\r\n".join(part for line in lines for part in _fold(line)) + "\r\n"
