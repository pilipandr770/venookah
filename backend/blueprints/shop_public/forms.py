# file: backend/blueprints/shop_public/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional


class SearchForm(FlaskForm):
    query = StringField("Пошук", validators=[Optional()])
    submit = SubmitField("Шукати")
