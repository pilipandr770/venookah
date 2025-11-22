# file: backend/services/order_service.py

from decimal import Decimal
from typing import Iterable

from ..extensions import db
from ..models.order import Order, OrderItem, OrderStatus
from ..models.product import Product
from ..models.user import User


def create_order(
    user: User,
    items: list[dict],
    currency: str = "EUR",
    is_b2b: bool | None = None,
) -> Order:
    """
    Створює замовлення.

    items = [
        {"product": <Product>, "quantity": 10},
        ...
    ]
    """
    if is_b2b is None:
        is_b2b = bool(user.is_b2b)

    order = Order(
        user_id=user.id,
        status=OrderStatus.NEW,
        currency=currency,
        is_b2b=is_b2b,
    )
    db.session.add(order)
    db.session.flush()  # отримати order.id

    total = Decimal("0.00")

    for item in items:
        product: Product = item["product"]
        quantity: int = int(item.get("quantity", 1))

        price = product.price_b2b if is_b2b else product.price_b2c
        price = price or Decimal("0.00")

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=price,
            currency=currency,
        )
        db.session.add(order_item)
        total += price * quantity

    order.total_amount = total
    db.session.commit()
    return order


def get_orders_for_user(user: User) -> Iterable[Order]:
    """
    Повертає всі замовлення користувача.
    """
    return Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
