# file: backend/blueprints/admin/forms.py

import re
from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    DecimalField,
    BooleanField,
    SubmitField,
    SelectField,
    FileField,
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError

from ...models.product import Category, Product


def slugify(text: str) -> str:
    """Convert text to slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    return text


def validate_unique_slug(model, exclude_id=None):
    def _validate_unique_slug(form, field):
        query = model.query.filter_by(slug=field.data)
        if exclude_id:
            query = query.filter(model.id != exclude_id)
        if query.first():
            raise ValidationError(f"Slug '{field.data}' вже використовується.")
    return _validate_unique_slug


class CategoryForm(FlaskForm):
    name = StringField(
        "Назва категорії",
        validators=[DataRequired(), Length(max=255)],
    )
    slug = StringField(
        "Slug (URL-ідентифікатор)",
        validators=[DataRequired(), Length(max=255)],
    )
    description = TextAreaField("Опис", validators=[Optional()])
    image = FileField("Фото категорії", validators=[Optional()])
    parent_id = SelectField("Батьківська категорія", coerce=int, validators=[Optional()])
    submit = SubmitField("Зберегти")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add unique validation
        self.slug.validators.append(validate_unique_slug(Category, kwargs.get('obj').id if kwargs.get('obj') else None))


class ProductForm(FlaskForm):
    name = StringField(
        "Назва товару",
        validators=[DataRequired(), Length(max=255)],
    )
    slug = StringField(
        "Slug (URL-ідентифікатор)",
        validators=[DataRequired(), Length(max=255)],
    )
    description = TextAreaField("Опис", validators=[Optional()])

    category_id = SelectField(
        "Категорія",
        coerce=int,
        validators=[Optional()],
    )

    price_b2c = DecimalField(
        "Ціна B2C",
        default=Decimal("0.00"),
        places=2,
        rounding=None,
        validators=[DataRequired(), NumberRange(min=0)],
    )
    price_b2b = DecimalField(
        "Ціна B2B",
        default=Decimal("0.00"),
        places=2,
        rounding=None,
        validators=[DataRequired(), NumberRange(min=0)],
    )

    currency = StringField(
        "Валюта",
        default="EUR",
        validators=[DataRequired(), Length(max=8)],
    )

    is_active = BooleanField("Активний", default=True)

    main_image = FileField("Головне фото", validators=[Optional()])

    submit = SubmitField("Зберегти")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add unique validation
        self.slug.validators.append(validate_unique_slug(Product, kwargs.get('obj').id if kwargs.get('obj') else None))
