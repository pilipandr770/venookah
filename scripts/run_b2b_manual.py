# Run full B2B check for first B2B user (manual test)
import os
# Prevent the app startup hook from attempting to create default categories
os.environ.setdefault('ENSURE_DEFAULT_CATEGORIES', '0')

from backend.app import app
from backend.extensions import db
from backend.models.user import User
from backend.services.b2b_checks.b2b_service import run_b2b_checks_for_user

with app.app_context():
    # Avoid using ORM filter_by here because the model metadata includes a schema
    # which can produce schema-qualified SQL (e.g. "venookah2.users") that fails
    # on some local SQLite setups. Use a safe inspector check + raw SQL fallback.
    from sqlalchemy import inspect, text

    engine = getattr(db, 'engine', None) or db.get_engine()
    insp = inspect(engine)
    if not insp.has_table('users'):
        print('No `users` table found — have you run migrations?')
    else:
        # Try to find one B2B user via raw SQL (no schema prefix)
        row = db.session.execute(text("SELECT id, email FROM users WHERE is_b2b = 1 LIMIT 1")).fetchone()
        if not row:
            print('No B2B user found (is_b2b=1). Create one in admin or register via UI.')
        else:
            user_id, email = row[0], row[1]
            print('Running checks for:', email)
            # Load ORM user instance by primary key to avoid schema-qualified query in filter_by
            u = User.query.get(user_id)
            if not u:
                print('Could not load user ORM instance; aborting manual check')
            else:
                res = run_b2b_checks_for_user(u)
                if res is None:
                    print('No result returned')
                else:
                    print('score:', getattr(res, 'score', None))
                    print('screenshot_path:', getattr(res, 'screenshot_path', None))
                    raw = getattr(res, 'raw_osint', None) or {}
                    print('raw_osint keys:', list(raw.keys()))
