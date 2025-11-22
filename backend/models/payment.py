# file: backend/models/payment.py

from datetime import datetime

from ..extensions import db


class Payment(db.Model):
    __tablename__ = "payments"
    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("venookah2.orders.id"), nullable=False)
    order = db.relationship("Order", backref="payments")

    provider = db.Column(db.String(64), nullable=False, default="stripe")
    provider_payment_id = db.Column(db.String(255), nullable=True)
    provider_session_id = db.Column(db.String(255), nullable=True)

    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(8), nullable=False, default="EUR")

    status = db.Column(db.String(32), nullable=False, default="pending")

    raw_payload = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
