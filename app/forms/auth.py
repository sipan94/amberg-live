from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired, Length, ValidationError

from . import _l, max_len, strip

MIN_PASSWORD = 10


class _NewPassword:
    password = PasswordField(validators=[
        InputRequired(_l("required")),
        Length(min=MIN_PASSWORD, max=200, message=_l("password_length")),
    ])
    password2 = PasswordField(validators=[
        InputRequired(_l("required")),
        EqualTo("password", message=_l("password_match")),
    ])


def _email_field():
    return EmailField(filters=[strip], validators=[
        DataRequired(_l("required")), Email(_l("email")), max_len(254)])


class RegisterForm(_NewPassword, FlaskForm):
    email = _email_field()
    accept_terms = BooleanField(validators=[DataRequired(_l("accept_terms"))])

    def validate_password(self, field):
        if self.email.data and field.data and self.email.data.lower() in field.data.lower():
            raise ValidationError(_l("password_contains_email"))


class LoginForm(FlaskForm):
    email = _email_field()
    password = PasswordField(validators=[InputRequired(_l("required"))])


class ForgotPasswordForm(FlaskForm):
    email = _email_field()


class ResetPasswordForm(_NewPassword, FlaskForm):
    pass


class ChangePasswordForm(_NewPassword, FlaskForm):
    current_password = PasswordField(validators=[InputRequired(_l("required"))])


class DeleteAccountForm(FlaskForm):
    password = PasswordField(validators=[InputRequired(_l("required"))])
    confirm = BooleanField(validators=[DataRequired(_l("confirm_delete"))])


class SimpleForm(FlaskForm):
    """Just a CSRF token, for POST buttons (logout, resend, delete)."""
