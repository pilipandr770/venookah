# file: worker/tasks/low_stock_alerts.py

"""
Перевірка низьких залишків на складі і створення алертів.
"""

from backend.extensions import db
from backend.models.inventory import StockItem
from backend.services.alert_service import create_alert


LOW_STOCK_THRESHOLD = 50  # TODO: винести в конфіг


def run():
    low_stock_items = StockItem.query.filter(
        StockItem.quantity_total <= LOW_STOCK_THRESHOLD
    ).all()
    for item in low_stock_items:
        payload = {
            "product_id": item.product_id,
            "quantity_total": item.quantity_total,
            "location": item.location,
        }
        # TODO: реальний target (chat_id шефа)
        create_alert("low_stock", channel="telegram", target="owner_chat_id", payload=payload)

    db.session.remove()
