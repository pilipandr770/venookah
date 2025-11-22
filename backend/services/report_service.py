# file: backend/services/report_service.py

from datetime import datetime, timedelta

from ..models.order import Order
from ..models.user import User


def get_sales_summary(days: int = 7) -> dict:
    """
    Простий звіт по продажам за останні N днів.
    Пізніше можна розширити в PDF/Excel.
    """
    since = datetime.utcnow() - timedelta(days=days)
    orders = Order.query.filter(Order.created_at >= since).all()

    total_amount = sum([o.total_amount or 0 for o in orders])
    count = len(orders)

    return {
        "period_days": days,
        "orders_count": count,
        "total_amount": float(total_amount),
    }


def get_top_customers(limit: int = 5) -> list[dict]:
    """
    Простий список топ-клієнтів за сумою замовлень.
    (MVP — дуже спрощено, без складних SQL).
    """
    users: list[User] = User.query.all()
    results: list[dict] = []

    for u in users:
        total = sum([o.total_amount or 0 for o in u.orders])
        if total:
            results.append({"user": u, "total": float(total)})

    results.sort(key=lambda x: x["total"], reverse=True)
    return results[:limit]
