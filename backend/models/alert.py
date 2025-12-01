# file: backend/models/alert.py

from datetime import datetime

from ..extensions import db


class Alert(db.Model):
    __tablename__ = "alerts"

    

    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(db.String(64), nullable=False)  # low_stock, container_delay, etc.
    channel = db.Column(db.String(64), nullable=False, default="telegram")  # email/tg
    target = db.Column(db.String(255), nullable=True)  # email / chat_id

    payload = db.Column(db.JSON, nullable=True)
    is_sent = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
