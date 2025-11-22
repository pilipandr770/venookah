# file: worker/tasks/prepare_shipment.py

"""
Завдання для підготовки відправлення після оплати.
"""

from backend.extensions import db
from backend.models.order import Order, OrderStatus
from backend.models.inventory import StockItem
from backend.services.shipping.shipping_service import create_shipment_for_order


def prepare_shipment(order_id: int):
    """
    Підготовка відправлення: резервування товарів, створення shipment.
    """
    order = Order.query.get(order_id)
    if not order or order.status != OrderStatus.PAID:
        return

    # Резервувати товари на складі
    for item in order.items:
        stock = StockItem.query.filter_by(product_id=item.product_id).first()
        if stock and stock.available() >= item.quantity:
            stock.quantity_reserved += item.quantity
            db.session.add(stock)

    # Оновити статус на processing
    order.status = OrderStatus.PROCESSING
    db.session.commit()

    # Створити shipment, якщо ще не створено
    if not order.shipments:
        create_shipment_for_order(order, provider="dpd")
        order.status = OrderStatus.SHIPPED
        db.session.commit()