# file: backend/services/prepare_shipment.py

"""
Сервіс для підготовки відправлення після оплати.
"""

import logging

from ..extensions import db
from ..models.order import Order, OrderStatus
from ..models.inventory import StockItem
from ..models.warehouse import WarehouseTask
from .shipping.shipping_service import create_shipment_for_order

logger = logging.getLogger(__name__)


def prepare_shipment(order_id: int):
    """
    Підготовка відправлення: резервування товарів, створення shipment.
    """
    logger.info("prepare_shipment called for order_id=%s", order_id)
    order = Order.query.get(order_id)
    if not order:
        logger.warning("prepare_shipment: order not found: %s", order_id)
        return
    if order.status != OrderStatus.PAID:
        logger.info("prepare_shipment: order %s status is not PAID (%s)", order_id, order.status)
        return

    # Резервувати товари на складі
    for item in order.items:
        stock = StockItem.query.filter_by(product_id=item.product_id).first()
        if stock and stock.available() >= item.quantity:
            stock.quantity_reserved += item.quantity
            db.session.add(stock)
            logger.info("Reserved %s units of product_id=%s for order_id=%s", item.quantity, item.product_id, order.id)
        else:
            logger.warning("Insufficient stock for product_id=%s for order_id=%s", item.product_id, order.id)

    # Створити warehouse task
    task = WarehouseTask(order_id=order.id, status=WarehouseTaskStatus.PENDING)
    db.session.add(task)

    # Оновити статус на processing
    order.status = OrderStatus.PROCESSING
    db.session.commit()
    logger.info("Order %s status updated to PROCESSING and changes committed", order.id)

    # После коммита SQLAlchemy заполняет task.id — логируем для отладки
    logger.info("Created WarehouseTask id=%s for order_id=%s", getattr(task, 'id', None), order.id)

    # Створити shipment, якщо ще не створено
    if not order.shipments:
        create_shipment_for_order(order, provider="dpd")
        order.status = OrderStatus.SHIPPED
        db.session.commit()