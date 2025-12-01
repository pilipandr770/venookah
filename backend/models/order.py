# file: backend/models/order.py

from datetime import datetime

from ..extensions import db
from sqlalchemy import inspect




class OrderStatus:
    NEW = "new"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(db.Model):
    __tablename__ = "orders"

    

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="orders")

    status = db.Column(db.String(32), nullable=False, default=OrderStatus.NEW)

    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(8), nullable=False, default="EUR")

    is_b2b = db.Column(db.Boolean, nullable=False, default=False)

    shipping_address = db.Column(db.JSON, nullable=True)
    billing_address = db.Column(db.JSON, nullable=True)

    stripe_payment_intent_id = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    order = db.relationship("Order", backref="items")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product = db.relationship("Product")

    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(8), nullable=False, default="EUR")


class Cart(db.Model):
    __tablename__ = "carts"

    

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="cart")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class CartItem(db.Model):
    __tablename__ = "cart_items"

    

    id = db.Column(db.Integer, primary_key=True)

    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    cart = db.relationship("Cart", backref="items")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product = db.relationship("Product")

    quantity = db.Column(db.Integer, nullable=False, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# Listen for status changes to automatically prepare shipment when order becomes PAID
def _after_order_update(mapper, connection, target):
    try:
        hist = inspect(target).attrs.status.history
        # If status changed and new value is PAID
        if hist.has_changes() and hist.added and list(hist.added)[-1] == OrderStatus.PAID:
            # Import here to avoid circular imports at module import time
            from ..services.prepare_shipment import prepare_shipment

            # Call preparation (it will check order status and create task)
            prepare_shipment(target.id)
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Error in order after_update listener")


from sqlalchemy import event
event.listen(Order, 'after_update', _after_order_update)
