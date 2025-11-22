# file: backend/services/shipping/shipping_service.py

from datetime import datetime, timedelta
from typing import Literal

from ...extensions import db
from ...models.order import Order
from ...models.shipping import Shipment
from . import dhl_client, dpd_client

Provider = Literal["dhl", "dpd"]


def create_shipment_for_order(order: Order, provider: Provider = "dhl") -> Shipment:
    """
    Створює відправлення для замовлення через вибраного провайдера.
    (Поки що заглушка з псевдо-трекінгом).
    """
    if provider == "dpd":
        data = dpd_client.create_shipment(order.id)
    else:
        data = dhl_client.create_shipment(order.id)

    shipment = Shipment(
        order_id=order.id,
        provider=data["provider"],
        tracking_number=data["tracking_number"],
        status="created",
        label_url=data.get("label_url"),
        raw_payload=data.get("raw"),
        eta=datetime.utcnow() + timedelta(days=5),  # mock
    )
    db.session.add(shipment)
    db.session.commit()
    return shipment


def get_shipment_status(provider: Provider, tracking_number: str) -> dict:
    """
    Отримує статус відправлення по провайдеру та номеру.
    """
    if provider == "dpd":
        return dpd_client.get_shipment_status(tracking_number)
    else:
        return dhl_client.get_shipment_status(tracking_number)
