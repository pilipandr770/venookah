# file: worker/worker.py

"""
Заглушка воркера.

Пізніше сюди можна підключити RQ / Celery.
Поки що просто визначимо псевдо-інтерфейс виклику задач.
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
    Одноразовий запуск всіх задач (наприклад, з cron).
    """
    sync_b2b_checks.run()
    sync_shipping_status.run()
    sync_containers.run()
    low_stock_alerts.run()
    reports_daily.run()


if __name__ == "__main__":
    run_all_once()
