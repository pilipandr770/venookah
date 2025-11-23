# file: backend/extensions.py

from flask import current_app, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from sqlalchemy import text

# Initialisierung der Extension-Objekte (ohne App)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()


def _ensure_schema_exists():
    """
    Створює схему в Postgres, якщо її ще немає.
    Працює тільки якщо драйвер Postgres.
    """
    engine = db.engine
    url = engine.url

    # Перевіряємо, що це саме Postgres
    if not url.drivername.startswith("postgres"):
        return

    schema = current_app.config.get("DB_SCHEMA", "public")
    if not schema or schema == "public":
        return

    # CREATE SCHEMA IF NOT EXISTS <schema>;
    with engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        conn.commit()


def init_extensions(app):
    """Binde Erweiterungen an die Flask-Anwendung."""
    db.init_app(app)

    with app.app_context():
        # Створюємо схему в Postgres (якщо потрібно)
        _ensure_schema_exists()

    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    babel.init_app(app)
    # Register locale selector in a way that works across Flask-Babel versions.
    try:
        # Older Flask-Babel versions provide the decorator `localeselector`.
        # If available, use it to register the module-level `get_locale`.
        babel.localeselector(get_locale)  # type: ignore[attr-defined]
    except AttributeError:
        # Newer Flask-Babel versions use `locale_selector_func` assignment.
        setattr(babel, "locale_selector_func", get_locale)

    # Damit Flask-Login weiß, wie ein Benutzer geladen wird
    from .models.user import User  # noqa: WPS433,F401

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Inject alerts count into template context for admin UI (defensive)
    try:
        from .models.alert import Alert  # noqa: WPS433,F401

        @app.context_processor
        def inject_alerts_count():
            try:
                # Count unsent alerts to show a badge in the navbar
                cnt = 0
                try:
                    cnt = Alert.query.filter_by(is_sent=False).count()
                except Exception:
                    # Some local setups (SQLite without schema) may fail; swallow errors
                    cnt = 0
                return {'alerts_count': cnt}
            except Exception:
                return {'alerts_count': 0}
    except Exception:
        # If importing Alert fails (missing models/migrations), don't break startup
        @app.context_processor
        def inject_alerts_count():
            return {'alerts_count': 0}


def get_locale():
    """Wählt Locale basierend auf `?lang=` oder Accept-Language, Fallback auf config."""
    supported = current_app.config.get("SUPPORTED_LANGUAGES", ["de", "en"])
    # allow explicit override via query param (useful for QA)
    lang = request.args.get("lang")
    if lang and lang in supported:
        return lang

    match = request.accept_languages.best_match(supported)
    if match:
        return match

    return current_app.config.get("BABEL_DEFAULT_LOCALE", "de")
