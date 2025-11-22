# file: backend/blueprints/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=255)],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    remember_me = BooleanField("Запам'ятати мене")
    submit = SubmitField("Увійти")


class RegisterForm(FlaskForm):
    account_type = SelectField(
        "Тип акаунта",
        choices=[("b2c", "Приватний клієнт (B2C)"), ("b2b", "Бізнес-клієнт (B2B)")],
        validators=[DataRequired()],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=255)],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=6, max=128)],
    )
    password_confirm = PasswordField(
        "Підтвердження паролю",
        validators=[DataRequired(), EqualTo("password", message="Паролі не співпадають")],
    )

    first_name = StringField("Ім'я", validators=[Optional(), Length(max=120)])
    last_name = StringField("Прізвище", validators=[Optional(), Length(max=120)])
    company_name = StringField("Компанія", validators=[Optional(), Length(max=255)])
    vat_number = StringField("VAT номер", validators=[Optional(), Length(max=64)])
    handelsregister = StringField("Handelsregister", validators=[Optional(), Length(max=64)])
    country = StringField("Країна", validators=[Optional(), Length(max=64)])
    city = StringField("Місто", validators=[Optional(), Length(max=128)])
    address = StringField("Адреса", validators=[Optional(), Length(max=255)])
    postal_code = StringField("Поштовий індекс", validators=[Optional(), Length(max=32)])

    submit = SubmitField("Зареєструватися")
