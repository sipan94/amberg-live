"""Offers list and detail."""
from flask import render_template, request
from sqlalchemy import select

from ..extensions import db
from ..models import Offer
from ..services.offers import current_offers_query
from ..utils.timeutils import today_local
from . import bp
from .helpers import count_view, get_visible_or_404

PER_PAGE = 12


@bp.get("/angebote")
def offers():
    page = db.paginate(current_offers_query(), page=request.args.get("seite", 1, type=int),
                       per_page=PER_PAGE, error_out=False)
    return render_template("public/offers_list.html", page=page)


@bp.get("/angebote/<slug>")
def offer_detail(slug):
    offer = get_visible_or_404(db.session.scalar(select(Offer).where(Offer.slug == slug)))
    count_view(Offer, offer)
    today = today_local()
    expired = offer.valid_until is not None and offer.valid_until < today
    return render_template("public/offer_detail.html", offer=offer, expired=expired, today=today)
