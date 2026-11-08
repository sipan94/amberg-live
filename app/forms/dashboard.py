from datetime import datetime, time, timedelta

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import BooleanField, DateField, EmailField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Email, InputRequired, Length, Optional, Regexp, URL

from ..models import WEEKDAYS, OrgType
from ..utils import recurrence
from ..utils.timeutils import now_local
from . import _l, max_len, normalize_url, strip

MAX_DESCRIPTION = 5000
MAX_EVENT_DURATION = timedelta(days=60)
MAX_SERIES = timedelta(days=2 * 365)


def _rights_field():
    return BooleanField(validators=[DataRequired(_l("rights"))])


def _description_field(required=True):
    checks = [DataRequired(_l("required"))] if required else [Optional()]
    return TextAreaField(filters=[strip], validators=[*checks, max_len(MAX_DESCRIPTION)])


class OrganizationForm(FlaskForm):
    name = StringField(filters=[strip], validators=[
        DataRequired(_l("required")), Length(min=2, max=150, message=_l("length_2_150"))])
    org_type = SelectField(choices=[(OrgType.BUSINESS, ""), (OrgType.CLUB, "")],
                           validators=[InputRequired(_l("required"))])
    description = _description_field()
    address = StringField(filters=[strip], validators=[Optional(), max_len(255)])
    phone = StringField(filters=[strip], validators=[
        Optional(), Regexp(r"^[0-9 +()/\-]{5,30}$", message=_l("phone"))])
    email = EmailField(filters=[strip], validators=[Optional(), Email(_l("email")), max_len(254)])
    website = StringField(filters=[normalize_url], validators=[
        Optional(), URL(message=_l("url")), max_len(255)])
    logo = FileField()
    remove_logo = BooleanField()
    cover = FileField()
    remove_cover = BooleanField()
    rights_confirmed = _rights_field()


# Seven optional opening-hours fields: hours_mo ... hours_so
for _day in WEEKDAYS:
    setattr(OrganizationForm, f"hours_{_day}",
            StringField(filters=[strip], validators=[Optional(), max_len(60)]))


class EventForm(FlaskForm):
    title = StringField(filters=[strip], validators=[
        DataRequired(_l("required")), Length(min=3, max=150, message=_l("length_3_150"))])
    category_id = SelectField(coerce=int, validators=[InputRequired(_l("required"))])
    description = _description_field()
    start_date = DateField(validators=[InputRequired(_l("date"))])
    start_time = TimeField(format="%H:%M", validators=[InputRequired(_l("time"))])
    end_date = DateField(validators=[Optional()])
    end_time = TimeField(format="%H:%M", validators=[Optional()])
    recurrence = SelectField(choices=[(r, "") for r in recurrence.RULES], default=recurrence.NONE)
    recurrence_until = DateField(validators=[Optional()])
    location_name = StringField(filters=[strip], validators=[DataRequired(_l("required")), max_len(150)])
    address = StringField(filters=[strip], validators=[Optional(), max_len(255)])
    is_free = BooleanField(default=True)
    price_info = StringField(filters=[strip], validators=[Optional(), max_len(100)])
    image = FileField()
    remove_image = BooleanField()
    rights_confirmed = _rights_field()

    original_start: datetime | None = None  # set by the view when editing

    @property
    def start_at(self) -> datetime:
        return datetime.combine(self.start_date.data, self.start_time.data)

    @property
    def end_at(self) -> datetime | None:
        if not (self.end_date.data or self.end_time.data):
            return None
        return datetime.combine(self.end_date.data or self.start_date.data,
                                self.end_time.data or time(23, 59))

    def validate(self, extra_validators=None) -> bool:
        if not super().validate(extra_validators):
            return False
        ok = True
        start, end = self.start_at, self.end_at

        # New dates must not lie in the past; an unchanged old date may stay when editing.
        if start != self.original_start and start < now_local() - timedelta(hours=1):
            self.start_date.errors.append(str(_l("start_past")))
            ok = False
        if end is not None:
            if end <= start:
                self.end_time.errors.append(str(_l("end_before_start")))
                ok = False
            elif end - start > MAX_EVENT_DURATION:
                self.end_date.errors.append(str(_l("too_long_duration")))
                ok = False

        if self.recurrence.data != recurrence.NONE:
            limit = timedelta(days=7 if self.recurrence.data == recurrence.WEEKLY else 28)
            if end is not None and end - start >= limit:
                self.end_date.errors.append(str(_l("recurring_too_long")))
                ok = False
            until = self.recurrence_until.data
            if until and until < self.start_date.data:
                self.recurrence_until.errors.append(str(_l("until_before_start")))
                ok = False
            elif until and until - self.start_date.data > MAX_SERIES:
                self.recurrence_until.errors.append(str(_l("series_too_long")))
                ok = False
        return ok


class OfferForm(FlaskForm):
    title = StringField(filters=[strip], validators=[
        DataRequired(_l("required")), Length(min=3, max=150, message=_l("length_3_150"))])
    description = _description_field()
    valid_from = DateField(validators=[InputRequired(_l("date"))])
    valid_until = DateField(validators=[Optional()])
    image = FileField()
    remove_image = BooleanField()
    rights_confirmed = _rights_field()

    def validate(self, extra_validators=None) -> bool:
        if not super().validate(extra_validators):
            return False
        until = self.valid_until.data
        if until and until < self.valid_from.data:
            self.valid_until.errors.append(str(_l("until_before_start")))
            return False
        if until and until < now_local().date():
            self.valid_until.errors.append(str(_l("offer_expired")))
            return False
        return True
