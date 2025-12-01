# file: backend/models/shipping.py

from datetime import datetime

from ..extensions import db


class Shipment(db.Model):
    __tablename__ = "shipments"

    

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    order = db.relationship("Order", backref="shipments")

    provider = db.Column(db.String(64), nullable=False)  # dhl, dpd, etc.
    tracking_number = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(64), nullable=False, default="created")

    label_url = db.Column(db.String(512), nullable=True)
    raw_payload = db.Column(db.JSON, nullable=True)

    eta = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
