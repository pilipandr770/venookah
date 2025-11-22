# file: backend/services/b2b_checks/vies_client.py

"""
Клієнт для перевірки VAT через VIES.

MVP: заглушка, яка повертає "is_valid=True", якщо vat_number не порожній.
Пізніше можна підключити реальний SOAP/REST клієнт.
"""

from typing import Any


def check_vat(vat_number: str, country_code: str | None = None) -> dict[str, Any]:
    if not vat_number:
        return {
            "is_valid": False,
            "company_name": None,
            "address": None,
            "raw": {"mock": True},
        }

    return {
        "is_valid": True,
        "company_name": f"Mock Company for {vat_number}",
        "address": "Mock Address, Europe",
        "raw": {"mock": True, "vat_number": vat_number, "country_code": country_code},
    }
