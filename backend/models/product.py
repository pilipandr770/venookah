# file: backend/models/product.py

from datetime import datetime

from ..extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(512))  # URL фото категории
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    parent = db.relationship("Category", remote_side=[id], backref="children")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Category {self.id} {self.name}>"


class Product(db.Model):
    """
    Товар. У нашому кейсі: вугілля або тютюн для кальянів.
    """

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    category = db.relationship("Category", backref="products")

    # ціна для B2C та B2B окремо
    price_b2c = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    price_b2b = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    currency = db.Column(db.String(8), nullable=False, default="EUR")

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # прості поля для фото
    main_image_url = db.Column(db.String(512))
    extra_images = db.Column(db.JSON)  # список URL-ів

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Product {self.id} {self.name}>"
