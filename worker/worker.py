# file: worker/worker.py

"""
Worker-Platzhalter.

Später kann hier RQ / Celery angebunden werden.
Vorerst definieren wir ein Pseudo-Interface zum Ausführen von Tasks.
"""

from tasks import (
    sync_b2b_checks,
    sync_shipping_status,
    sync_containers,
    low_stock_alerts,
    reports_daily,
)


def run_all_once():
    """
    Einmaliger Lauf aller Tasks (z. B. per cron).
    """
    sync_b2b_checks.run()
    sync_shipping_status.run()
    sync_containers.run()
    low_stock_alerts.run()
    reports_daily.run()


if __name__ == "__main__":
    run_all_once()
