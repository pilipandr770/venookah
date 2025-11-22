# file: backend/services/alert_service.py

from datetime import datetime
from typing import Literal

from ..extensions import db
from ..models.alert import Alert

Channel = Literal["telegram", "email", "signal"]


def create_alert(
    type_: str,
    channel: Channel,
    target: str,
    payload: dict | None = None,
) -> Alert:
    """
    Створює запис алерту. Надсилання фактичного повідомлення
    потім виконає воркер.
    """
    alert = Alert(
        type=type_,
        channel=channel,
        target=target,
        payload=payload or {},
        is_sent=False,
    )
    db.session.add(alert)
    db.session.commit()
    return alert


def mark_alert_sent(alert: Alert) -> None:
    """
    Позначає алерт як відправлений.
    """
    alert.is_sent = True
    alert.sent_at = datetime.utcnow()
    db.session.commit()
