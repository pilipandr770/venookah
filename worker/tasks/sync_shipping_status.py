# file: worker/tasks/sync_shipping_status.py

"""
Оновлення статусів відправлень.
"""

from backend.extensions import db
from backend.models.shipping import Shipment
from backend.services.shipping.dhl_client import get_shipment_status as dhl_status
from backend.services.shipping.dpd_client import get_shipment_status as dpd_status


def run():
    shipments = Shipment.query.all()
    for sh in shipments:
        if sh.provider == "dhl":
            data = dhl_status(sh.tracking_number)
        elif sh.provider == "dpd":
            data = dpd_status(sh.tracking_number)
        else:
            continue

        sh.status = data.get("status", sh.status)
        sh.raw_payload = data.get("raw", sh.raw_payload)
    db.session.commit()
    db.session.remove()
