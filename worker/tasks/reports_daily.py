# file: worker/tasks/reports_daily.py

"""
Täglicher Bericht an den Inhaber (zukünftig via KI/Bot).
"""

from backend.services.report_service import get_sales_summary


def run():
    summary = get_sales_summary(days=1)
    # TODO: an den Inhaber via Telegram/Signal senden
    print("[DAILY REPORT MOCK]", summary)
