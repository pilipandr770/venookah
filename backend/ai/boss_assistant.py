# file: backend/ai/boss_assistant.py

"""
Інтерфейс до AI-асистента для шефа, який читає дані з БД і формує звіти.
"""

from .assistant_client import assistant_client
from ..services.report_service import get_sales_summary


def generate_sales_report_text(days: int = 7) -> str:
    summary = get_sales_summary(days=days)
    base_text = (
        f"За останні {summary['period_days']} днів: "
        f"{summary['orders_count']} замовлень, "
        f"загальна сума {summary['total_amount']} EUR."
    )
    return assistant_client.ask_boss_assistant(base_text, context=summary)
