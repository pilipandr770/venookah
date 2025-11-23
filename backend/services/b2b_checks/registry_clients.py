# file: backend/services/b2b_checks/registry_clients.py

"""
Clients für nationale Register (Handelsregister, KVK, CVR, etc.).

MVP: Stub, der `is_found=True` zurückgibt, wenn ein Firmenname vorhanden ist.
"""

from typing import Any


def check_company_in_registry(
    company_name: str | None,
    handelsregister: str | None = None,
    country_code: str | None = None,
) -> dict[str, Any]:
    if not company_name and not handelsregister:
        return {
            "is_found": False,
            "raw": {"mock": True},
        }

    return {
        "is_found": True,
        "raw": {
            "mock": True,
            "company_name": company_name,
            "handelsregister": handelsregister,
            "country_code": country_code,
        },
    }
