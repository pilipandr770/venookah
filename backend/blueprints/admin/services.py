# file: backend/blueprints/admin/services.py

"""
Services für das Admin-Panel:
- Aggregation von Statistiken
- Hilfsfunktionen für CRM/Bestellungen
"""

from datetime import datetime, timedelta

from ...models.order import Order
from ...models.payment import Payment
from ...models.user import User, UserRole
from ...models.b2b_check import B2BCheckResult
from ...models.crm import Company
from ...services.report_service import get_sales_summary, get_top_customers


def get_admin_dashboard_data() -> dict:
    """
    Daten für die Admin-Dashboard-Startseite.
    """
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    orders_today = Order.query.filter(Order.created_at >= today_start).all()
    payments_today = Payment.query.filter(Payment.created_at >= today_start).all()

    users_total = User.query.count()
    b2b_users = User.query.filter_by(is_b2b=True).count()
    companies_total = Company.query.count()

    summary_7d = get_sales_summary(days=7)
    summary_30d = get_sales_summary(days=30)
    top_customers = get_top_customers(limit=5)

    last_b2b_checks = (
        B2BCheckResult.query.order_by(B2BCheckResult.created_at.desc())
        .limit(10)
        .all()
    )

    data = {
        "orders_today": orders_today,
        "payments_today": payments_today,
        "users_total": users_total,
        "b2b_users": b2b_users,
        "companies_total": companies_total,
        "summary_7d": summary_7d,
        "summary_30d": summary_30d,
        "top_customers": top_customers,
        "last_b2b_checks": last_b2b_checks,
    }
    return data
