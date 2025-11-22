# file: worker/tasks/reports_daily.py

"""
Щоденний звіт шефу (через AI/бота в майбутньому).
"""

from backend.services.report_service import get_sales_summary


def run():
    summary = get_sales_summary(days=1)
    # TODO: надіслати шефу через Telegram/Signal
    print("[DAILY REPORT MOCK]", summary)
