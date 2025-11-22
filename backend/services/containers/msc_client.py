# file: backend/services/containers/msc_client.py

"""
Заглушка для MSC API.

Тут потім можна реалізувати реальний HTTP-клієнт до myMSC.
"""

from datetime import datetime
from typing import Any


def get_container_status(container_number: str) -> dict[str, Any]:
    # TODO: реальна інтеграція з MSC
    return {
        "number": container_number,
        "status": "in_transit",
        "last_location": "Hamburg Port (mock)",
        "eta": datetime.utcnow(),
        "raw": {"mock": True},
    }
