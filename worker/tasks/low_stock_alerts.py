# file: worker/tasks/low_stock_alerts.py

"""
Prüft niedrige Lagerbestände und erzeugt Alerts.
"""

from backend.extensions import db
from backend.models.inventory import StockItem
from backend.services.alert_service import create_alert


LOW_STOCK_THRESHOLD = 50  # TODO: in Konfiguration auslagern


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
        # TODO: echtes Ziel (Chat-ID des Inhabers)
        create_alert("low_stock", channel="telegram", target="owner_chat_id", payload=payload)

    db.session.remove()
