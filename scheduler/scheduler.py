# file: scheduler/scheduler.py

"""
Platzhalter für den Scheduler.

Später kann APScheduler/cron innerhalb des Containers integriert werden.
"""

from worker.tasks import (
    sync_b2b_checks,
    sync_shipping_status,
    sync_containers,
    low_stock_alerts,
    reports_daily,
)


def run_all():
    sync_b2b_checks.run()
    sync_shipping_status.run()
    sync_containers.run()
    low_stock_alerts.run()
    reports_daily.run()


if __name__ == "__main__":
    run_all()
