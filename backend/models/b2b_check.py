# file: backend/models/b2b_check.py

from datetime import datetime

from ..extensions import db


class B2BCheckResult(db.Model):
    """
    Результати перевірки B2B-клієнта (VAT, реєстри, санкції).
    """

    __tablename__ = "b2b_check_results"
    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="b2b_checks")

    vat_number = db.Column(db.String(64), nullable=True)
    handelsregister = db.Column(db.String(64), nullable=True)
    country = db.Column(db.String(64), nullable=True)

    is_valid_vat = db.Column(db.Boolean, nullable=True)
    is_company_found = db.Column(db.Boolean, nullable=True)
    is_sanctioned = db.Column(db.Boolean, nullable=True)

    raw_vies = db.Column(db.JSON, nullable=True)
    raw_registry = db.Column(db.JSON, nullable=True)
    raw_osint = db.Column(db.JSON, nullable=True)

    score = db.Column(db.Integer, nullable=True)  # 0–100

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
