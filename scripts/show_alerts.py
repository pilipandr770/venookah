# Show recent alerts for admin review
import os
# Prevent the app startup hook from attempting to create default categories
os.environ.setdefault('ENSURE_DEFAULT_CATEGORIES', '0')

from backend.app import app
from backend.extensions import db
from sqlalchemy import text

with app.app_context():
    rows = db.session.execute(text("SELECT id, type, created_at, payload FROM alerts ORDER BY created_at DESC LIMIT 20")).fetchall()
    if not rows:
        print('No alerts found')
    for r in rows:
        print('ID:', r[0], 'type:', r[1], 'created_at:', r[2])
        print('payload:', r[3])
        print('-' * 40)
