# file: worker/tasks/sync_b2b_checks.py

"""
Пере-перевірка B2B-клієнтів за розкладом (MVP заглушка).
"""

from backend.extensions import db
from backend.models.user import User
from backend.services.b2b_checks.b2b_service import run_b2b_checks_for_user


def run():
    b2b_users = User.query.filter_by(is_b2b=True).all()
    for u in b2b_users:
        run_b2b_checks_for_user(u)
    db.session.remove()
