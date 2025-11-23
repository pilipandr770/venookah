# file: backend/ai/boss_assistant.py

"""
Schnittstelle zum KI-Assistenten für den Inhaber, der Daten aus der DB liest und Berichte erstellt.
"""

from .assistant_client import assistant_client
from ..services.report_service import get_sales_summary


def generate_sales_report_text(days: int = 7) -> str:
    summary = get_sales_summary(days=days)
    base_text = (
        f"In den letzten {summary['period_days']} Tagen: "
        f"{summary['orders_count']} Bestellungen, "
        f"Gesamtsumme {summary['total_amount']} EUR."
    )
    return assistant_client.ask_boss_assistant(base_text, context=summary)
