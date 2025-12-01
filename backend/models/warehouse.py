# file: backend/models/warehouse.py

from datetime import datetime

from ..extensions import db


class WarehouseTaskStatus:
    PENDING = "pending"
    ASSEMBLING = "assembling"
    PACKING = "packing"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class WarehouseTask(db.Model):
    __tablename__ = "warehouse_tasks"

    

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    order = db.relationship("Order", backref="warehouse_tasks")

    status = db.Column(db.String(32), nullable=False, default=WarehouseTaskStatus.PENDING)

    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    assigned_user = db.relationship("User", backref="warehouse_tasks")

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class WarehouseCategory(db.Model):
    __tablename__ = "warehouse_categories"

    

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    products = db.relationship("WarehouseProduct", back_populates="category", lazy=True)


class WarehouseProduct(db.Model):
    __tablename__ = "warehouse_products"

    

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("warehouse_categories.id"), nullable=True)
    category = db.relationship("WarehouseCategory", back_populates="products")

    quantity = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(255), nullable=True)  # место на складе

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
