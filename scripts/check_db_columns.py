# Small helper: check that new DB columns exist
import os
# Prevent the app startup hook from attempting to create default categories
# (may run before migrations are applied in dev/test environments).
os.environ.setdefault('ENSURE_DEFAULT_CATEGORIES', '0')

from backend.app import app
from backend.extensions import db
from sqlalchemy import inspect

with app.app_context():
    # Use the modern engine attribute instead of deprecated get_engine()
    engine = getattr(db, 'engine', None) or db.get_engine()
    insp = inspect(engine)
    print("users columns:")
    # Do not pass a schema for SQLite; let SQLAlchemy determine the right context.
    for c in insp.get_columns('users'):
        print(' ', c['name'])
    print('\nb2b_check_results columns:')
    for c in insp.get_columns('b2b_check_results'):
        print(' ', c['name'])
