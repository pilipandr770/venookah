# file: backend/services/shipping/dhl_client.py

"""
DHL API client.

Реалізує інтеграцію з DHL API для створення відправлень та отримання статусу.
"""

import requests
from flask import current_app
from typing import Any


def _get_api_key() -> str:
    return current_app.config.get("DHL_API_KEY", "")


def _get_base_url() -> str:
    return current_app.config.get("DHL_BASE_URL", "https://api.dhl.com")


def create_shipment(order_id: int) -> dict[str, Any]:
    """
    Створює відправлення через DHL API.
    Поки що заглушка.
    """
    api_key = _get_api_key()
    if not api_key:
        # Mock, якщо немає ключа
        return {
            "provider": "dhl",
            "tracking_number": f"DHL-TEST-{order_id}",
            "label_url": None,
            "raw": {"mock": True, "reason": "no_api_key"},
        }

    # TODO: Реальний виклик DHL API
    # Наприклад:
    # headers = {"Authorization": f"Bearer {api_key}"}
    # response = requests.post(f"{_get_base_url()}/shipments", json=payload, headers=headers)
    # ...

    return {
        "provider": "dhl",
        "tracking_number": f"DHL-{order_id}",
        "label_url": "https://example.com/label.pdf",
        "raw": {"mock": False},
    }


def get_shipment_status(tracking_number: str) -> dict[str, Any]:
    """
    Отримує статус відправлення по номеру.
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "tracking_number": tracking_number,
            "status": "unknown",
            "raw": {"mock": True, "reason": "no_api_key"},
        }

    # TODO: Реальний виклик
    # response = requests.get(f"{_get_base_url()}/track/{tracking_number}", headers={"Authorization": f"Bearer {api_key}"})

    return {
        "tracking_number": tracking_number,
        "status": "in_transit",
        "events": [
            {"date": "2023-11-01", "description": "Отправлено"},
            {"date": "2023-11-02", "description": "В пути"},
        ],
        "raw": {"mock": False},
    }
