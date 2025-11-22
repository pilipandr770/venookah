# file: backend/models/container.py

from datetime import datetime

from ..extensions import db


class Container(db.Model):
    """
    Морські контейнери (MSC).
    """

    __tablename__ = "containers"

    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)

    number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    provider = db.Column(db.String(64), nullable=False, default="msc")

    status = db.Column(db.String(128), nullable=True)
    last_location = db.Column(db.String(255), nullable=True)
    eta = db.Column(db.DateTime, nullable=True)
    route_info = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
