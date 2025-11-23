# file: backend/models/audit.py

from datetime import datetime

from ..extensions import db


class AuditLog(db.Model):
    """
    Audit-Protokoll der Administratoraktionen (wer was im Admin-Panel gemacht hat).
    """

    __tablename__ = "audit_logs"

    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("venookah2.users.id"), nullable=True)
    user = db.relationship("User", backref="audit_logs")

    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
