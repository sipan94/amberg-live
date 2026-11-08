from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp

from . import _l, max_len, strip

CATEGORY_ICONS = ["music", "family", "sport", "food", "culture", "market", "club", "other",
                  "star", "heart", "calendar", "tag", "store", "globe"]


class RejectForm(FlaskForm):
    reason = TextAreaField(filters=[strip], validators=[
        DataRequired(_l("reason_required")), Length(min=5, max=500, message=_l("reason_length"))])


class PremiumForm(FlaskForm):
    until = DateField(validators=[Optional()])


class CategoryForm(FlaskForm):
    name = StringField(filters=[strip], validators=[DataRequired(_l("required")), max_len(80)])
    icon = SelectField(choices=[(i, i) for i in CATEGORY_ICONS])
    color = StringField(filters=[strip], validators=[
        DataRequired(_l("required")), Regexp(r"^#[0-9a-fA-F]{6}$", message=_l("color"))])
    sort_order = IntegerField(default=0, validators=[Optional(), NumberRange(min=0, max=999)])
