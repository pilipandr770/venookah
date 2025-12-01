# file: backend/models/crm.py

from datetime import datetime

from ..extensions import db


class Company(db.Model):
    __tablename__ = "companies"

    

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)
    vat_number = db.Column(db.String(64), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(128), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    postal_code = db.Column(db.String(32), nullable=True)

    # Verknüpfung zum Benutzer (B2B)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref="company", primaryjoin="Company.user_id == User.id")

    extra = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Contact(db.Model):
    __tablename__ = "contacts"

    

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    company = db.relationship("Company", backref="contacts")

    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(64), nullable=True)

    role = db.Column(db.String(128), nullable=True)  # Manager, Einkäufer, etc.

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
