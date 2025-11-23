# file: worker/tasks/prepare_shipment.py

"""
Aufgabe zur Vorbereitung einer Sendung nach Zahlungseingang.
"""

from backend.extensions import db
from backend.models.order import Order, OrderStatus
from backend.models.inventory import StockItem
from backend.services.shipping.shipping_service import create_shipment_for_order


def prepare_shipment(order_id: int):
    """
    Vorbereitung der Sendung: Reservierung der Artikel und Erstellung des Shipments.
    """
    order = Order.query.get(order_id)
    if not order or order.status != OrderStatus.PAID:
        return

    # Artikel im Lager reservieren
    for item in order.items:
        stock = StockItem.query.filter_by(product_id=item.product_id).first()
        if stock and stock.available() >= item.quantity:
            stock.quantity_reserved += item.quantity
            db.session.add(stock)

    # Status auf 'processing' aktualisieren
    order.status = OrderStatus.PROCESSING
    db.session.commit()

    # Shipment erstellen, falls noch nicht vorhanden
    if not order.shipments:
        create_shipment_for_order(order, provider="dpd")
        order.status = OrderStatus.SHIPPED
        db.session.commit()