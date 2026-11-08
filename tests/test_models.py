"""Models and pure helpers: passwords, slugs, recurrence, sanitizing, calendar export."""
from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from app.extensions import db
from app.models import DailyStat, Event, Offer, Organization, User
from app.services.ics import event_to_ics
from app.utils.html import html_to_text, sanitize_html, text_to_html, to_plain_text
from app.utils.recurrence import add_months, iter_occurrences
from app.utils.slugs import make_slug


# ---- users ----------------------------------------------------------------------

def test_password_is_hashed_with_argon2(db_do, make):
    uid = make.user("a@example.com")
    user = db_do(lambda: db.session.get(User, uid))
    assert user.password_hash.startswith("$argon2")
    assert "test-passwort" not in user.password_hash
    assert db_do(lambda: db.session.get(User, uid).check_password("test-passwort-123"))
    assert not db_do(lambda: db.session.get(User, uid).check_password("wrong"))


def test_email_is_normalized(db_do, make):
    uid = make.user("  Mixed.Case@Example.COM ")
    assert db_do(lambda: db.session.get(User, uid).email) == "mixed.case@example.com"


def test_blocked_user_is_inactive(db_do, make):
    uid = make.user("b@example.com", blocked=True)
    assert db_do(lambda: db.session.get(User, uid).is_active) is False


def test_deleting_user_cascades_to_content(db_do, make):
    uid = make.user()
    org = make.org(uid)
    make.event(org)
    make.offer(org)

    def delete():
        db.session.delete(db.session.get(User, uid))
        db.session.commit()
        return [db.session.scalar(select(func.count(m.id))) for m in (Organization, Event, Offer)]

    assert db_do(delete) == [0, 0, 0]


# ---- slugs ------------------------------------------------------------------------

def test_slug_handles_umlauts():
    assert make_slug("Führung über Straße") == "fuehrung-ueber-strasse"
    assert make_slug("!!!") == "eintrag"


def test_slugs_are_unique_and_events_contain_date(db_do, make):
    org = make.org(make.user())
    a, b = make.event(org, title="Flohmarkt"), make.event(org, title="Flohmarkt")
    slugs = db_do(lambda: [db.session.get(Event, i).slug for i in (a, b)])
    assert slugs[0] != slugs[1]
    assert slugs[0].startswith("flohmarkt-20")


# ---- recurrence ---------------------------------------------------------------------

def test_monthly_rule_clamps_to_last_day():
    start = datetime(2026, 1, 31, 11, 0)
    days = [add_months(start, n).day for n in range(4)]
    assert days == [31, 28, 31, 30]
    assert add_months(datetime(2026, 11, 15), 3) == datetime(2027, 2, 15)


def test_weekly_occurrences_inside_window():
    start = datetime(2026, 1, 3, 7, 0)  # a Saturday
    window = (datetime(2026, 11, 1), datetime(2026, 11, 30))
    occ = list(iter_occurrences(start, start + timedelta(hours=5), "weekly", None, *window))
    assert [o[0].day for o in occ] == [7, 14, 21, 28]
    assert all(o[0].weekday() == 5 for o in occ)


def test_series_stops_at_until_date():
    start = datetime(2026, 11, 2, 18, 0)
    occ = list(iter_occurrences(start, None, "weekly", date(2026, 11, 16),
                                datetime(2026, 11, 1), datetime(2026, 12, 31)))
    assert [o[0].day for o in occ] == [2, 9, 16]


def test_ongoing_multi_day_event_overlaps_window():
    start, end = datetime(2026, 11, 26, 11), datetime(2026, 12, 23, 20)
    occ = list(iter_occurrences(start, end, "none", None, datetime(2026, 12, 5), datetime(2026, 12, 6)))
    assert occ == [(start, end)]


# ---- offers & stats ---------------------------------------------------------------------

def test_offer_validity(db_do, make):
    oid = make.offer(make.org(make.user()), days_from=0, days_until=3)
    offer = db_do(lambda: db.session.get(Offer, oid))
    today = offer.valid_from
    assert offer.is_valid_on(today) and offer.is_valid_on(today + timedelta(days=3))
    assert not offer.is_valid_on(today + timedelta(days=4))


def test_daily_stat_bump_counts_up(app, db_do):
    def bump_three_times():
        for _ in range(3):
            DailyStat.bump("page:home", date(2026, 11, 8))
            db.session.commit()
        return db.session.scalar(select(DailyStat.count).where(DailyStat.key == "page:home"))

    assert db_do(bump_three_times) == 3


# ---- HTML -------------------------------------------------------------------------------------

def test_sanitizer_removes_scripts_and_handlers():
    dirty = '<p onclick="x()">Hi<script>alert(1)</script> <a href="javascript:evil()">x</a></p>'
    clean = sanitize_html(dirty)
    assert "script" not in clean and "onclick" not in clean and "javascript:" not in clean


def test_links_get_safe_rel():
    html = sanitize_html('<p>Siehe https://example.com</p>')
    assert 'rel="' in html and "nofollow" in html and "noopener" in html


def test_textarea_roundtrip():
    text = "Erster Absatz\nzweite Zeile\n\nZweiter Absatz"
    html = text_to_html(text)
    assert html.startswith("<p>Erster Absatz<br>zweite Zeile</p>")
    assert html_to_text(html) == text
    # Editing and saving repeatedly must not change the text (no growing blank lines).
    assert text_to_html(html_to_text(text_to_html(html_to_text(html)))) == html


def test_plain_text_truncates_on_word():
    assert to_plain_text("<p>eins zwei drei vier</p>", 12) == "eins zwei…"


# ---- calendar export ------------------------------------------------------------------------------

def test_ics_for_monthly_event_on_31st(db_do, make):
    org = make.org(make.user())
    eid = make.event(org, title="Stammtisch; mit, Sonderzeichen", recurrence="monthly")

    def build():
        ev = db.session.get(Event, eid)
        ev.start_at = ev.start_at.replace(year=2027, month=1, day=31)
        ev.description = "<p>" + "Sehr langer Text " * 20 + "</p>"
        return event_to_ics(ev, url="https://example.com/x", host="example.com")

    ics = db_do(build)
    assert "BEGIN:VEVENT" in ics and "\r\n" in ics
    assert "RRULE:FREQ=MONTHLY;BYMONTHDAY=28,29,30,31;BYSETPOS=-1" in ics
    assert r"SUMMARY:Stammtisch\; mit\, Sonderzeichen" in ics
    assert "BEGIN:VTIMEZONE" in ics and "DTSTART;TZID=Europe/Berlin:20270131T190000" in ics
    assert all(len(line.encode()) <= 75 for line in ics.split("\r\n"))
