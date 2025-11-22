# file: backend/models/auth.py

from datetime import datetime, timedelta

from ..extensions import db


class EmailConfirmationToken(db.Model):
    """
    Токени підтвердження email (опціонально, на майбутнє).
    """

    __tablename__ = "email_confirmation_tokens"

    __table_args__ = {'schema': 'venookah2'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("venookah2.users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at

    @staticmethod
    def expiry(default_hours: int = 24) -> datetime:
        return datetime.utcnow() + timedelta(hours=default_hours)
