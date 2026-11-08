"""Directory of businesses and clubs, and their profile pages."""
from datetime import timedelta

from flask import abort, render_template, request
from flask_login import current_user
from sqlalchemy import or_, select

from ..extensions import db
from ..models import WEEKDAYS, Offer, Organization, OrgType, Status, User
from ..services.events import EventFilter, find_occurrences, first_per_event
from ..services.stats import track
from ..utils.timeutils import now_local
from . import bp

PER_PAGE = 18
TYPE_PARAM = {"geschaefte": OrgType.BUSINESS, "vereine": OrgType.CLUB}


def public_orgs():
    return (select(Organization).join(Organization.owner)
            .where(Organization.status == Status.APPROVED, User.is_blocked.is_(False)))


@bp.get("/geschaefte-vereine")
def organizations():
    typ = request.args.get("typ", "")
    q = " ".join(request.args.get("q", "").split())[:100]
    stmt = public_orgs()
    if typ in TYPE_PARAM:
        stmt = stmt.where(Organization.org_type == TYPE_PARAM[typ])
    if q:
        stmt = stmt.where(or_(Organization.name.icontains(q, autoescape=True),
                              Organization.description.icontains(q, autoescape=True)))
    stmt = stmt.order_by(Organization.is_premium.desc(), Organization.name)
    page = db.paginate(stmt, page=request.args.get("seite", 1, type=int),
                       per_page=PER_PAGE, error_out=False)
    return render_template("public/orgs_list.html", page=page, typ=typ, q=q)


@bp.get("/geschaefte-vereine/<slug>")
def organization_detail(slug):
    org = db.session.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        abort(404)
    owner_or_admin = current_user.is_authenticated and (
        current_user.is_admin or org.owner_id == current_user.id)
    if not (org.is_public or owner_or_admin):
        abort(404)

    if org.is_public:
        track(f"organization:{org.id}")
    now = now_local()
    events = first_per_event(find_occurrences(
        EventFilter(now, now + timedelta(days=180), organization_id=org.id)))[:12]
    today = now.date()
    offers = [o for o in org.offers
              if o.is_approved and (o.valid_until is None or o.valid_until >= today)]
    hours = [(t_key, org.opening_hours[t_key]) for t_key in WEEKDAYS
             if org.opening_hours and org.opening_hours.get(t_key)]
    return render_template("public/org_detail.html", org=org, events=events, offers=offers,
                           hours=hours, today=today)
