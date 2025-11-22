# file: backend/services/b2b_checks/osint_client.py

"""
OSINT / санкційні перевірки.

MVP: заглушка, яка завжди повертає is_sanctioned=False.
"""

from typing import Any


def check_sanctions(vat_number: str | None, company_name: str | None) -> dict[str, Any]:
    return {
        "is_sanctioned": False,
        "raw": {
            "mock": True,
            "vat_number": vat_number,
            "company_name": company_name,
        },
    }
