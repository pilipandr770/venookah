# file: backend/services/shipping/dpd_client.py

"""
DPD API client.

Реалізує інтеграцію з DPD API для створення відправлень та отримання статусу.
"""

import requests
from flask import current_app
from typing import Any, Optional
import time

# Кеш для токена
_token_cache = {"token": None, "expires": 0}


def _get_api_credentials() -> dict[str, str]:
    return {
        "delisId": current_app.config.get("DPD_DELIS_ID", "sandboxdpd"),
        "password": current_app.config.get("DPD_PASSWORD", "xMmshh1"),
        "messageLanguage": current_app.config.get("DPD_MESSAGE_LANGUAGE", "de_DE"),
    }


def _get_base_url() -> str:
    return current_app.config.get("DPD_BASE_URL", "https://public-ws-stage.dpd.com")


def _get_auth_token() -> Optional[str]:
    """
    Отримує токен аутентифікації DPD.
    Кешує токен на день.
    """
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]

    credentials = _get_api_credentials()
    url = f"{_get_base_url()}/services/LoginService/V2_0/getAuth"
    payload = {
        "delisId": credentials["delisId"],
        "password": credentials["password"],
        "messageLanguage": credentials["messageLanguage"],
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if token:
            # Токен действителен до 03:00 CET, но для простоты кеш на 24 часа
            _token_cache["token"] = token
            _token_cache["expires"] = now + 86400  # 24 hours
        return token
    except Exception as e:
        current_app.logger.error(f"DPD auth error: {e}")
        return None


def create_shipment(order_id: int) -> dict[str, Any]:
    """
    Створює відправлення через DPD API.
    Поки що заглушка, бо SOAP складний.
    """
    # TODO: Реалізувати через SOAP ShipmentService 4.4
    return {
        "provider": "dpd",
        "tracking_number": f"DPD-{order_id}",
        "label_url": None,  # TODO: отримати URL label
        "raw": {"mock": True, "reason": "soap_not_implemented"},
    }


def get_shipment_status(tracking_number: str) -> dict[str, Any]:
    """
    Отримує статус відправлення по номеру через DPD REST API.
    """
    token = _get_auth_token()
    if not token:
        return {
            "tracking_number": tracking_number,
            "status": "auth_failed",
            "raw": {"error": "no_token"},
        }

    url = f"{_get_base_url()}/restservices/ShipmentService/V4_4/getTrackingData"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"parcelLabelNumber": tracking_number}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Парсинг відповіді DPD
        status = data.get("status", "unknown")
        events = []
        if "events" in data:
            for event in data["events"]:
                events.append({
                    "date": event.get("date"),
                    "description": event.get("description", ""),
                })

        return {
            "tracking_number": tracking_number,
            "status": status,
            "events": events,
            "raw": data,
        }
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"DPD tracking error: {e}")
        return {
            "tracking_number": tracking_number,
            "status": "error",
            "raw": {"error": str(e)},
        }
