# file: backend/services/b2b_checks/osint_client.py

"""
OSINT / санкційні перевірки.

MVP: заглушка, яка завжди повертає is_sanctioned=False.
"""

from typing import Any, Optional

from .osint_browser import capture_site_snapshot


def check_sanctions(vat_number: str | None, company_name: str | None, website: Optional[str] = None) -> dict[str, Any]:
    """
    Perform OSINT checks. MVP: try to capture site screenshot and return result dict.

    Returns structure with keys: is_sanctioned (bool), raw (dict), screenshot (optional path)
    """
    res: dict[str, Any] = {
        "is_sanctioned": False,
        "raw": {
            "mock": True,
            "vat_number": vat_number,
            "company_name": company_name,
        },
    }

    if website:
        try:
            snap = capture_site_snapshot(website)
            res["raw"]["site_snapshot"] = snap
            if snap.get("success"):
                res["screenshot"] = snap.get("path")
        except Exception:
            # swallow errors — OSINT should not block registration
            res["raw"]["site_snapshot_error"] = "failed"

    return res
