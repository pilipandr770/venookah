# file: backend/services/prepare_shipment.py

"""
Сервіс для підготовки відправлення після оплати.
"""

from ..extensions import db
from ..models.order import Order, OrderStatus
from ..models.inventory import StockItem
from ..models.warehouse import WarehouseTask
from .shipping.shipping_service import create_shipment_for_order


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

    # Створити warehouse task
    task = WarehouseTask(order_id=order.id, status="pending")
    db.session.add(task)

    # Оновити статус на processing
    order.status = OrderStatus.PROCESSING
    db.session.commit()

    # Створити shipment, якщо ще не створено
    if not order.shipments:
        create_shipment_for_order(order, provider="dpd")
        order.status = OrderStatus.SHIPPED
        db.session.commit()