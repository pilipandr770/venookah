# file: backend/extensions.py

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from sqlalchemy import text

# Ініціалізація об'єктів розширень (без app)
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
    """Підключаємо розширення до Flask-додатку."""
    db.init_app(app)

    with app.app_context():
        # Створюємо схему в Postgres (якщо потрібно)
        _ensure_schema_exists()

    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    babel.init_app(app)

    # Щоб Flask-Login знав, як завантажувати користувача
    from .models.user import User  # noqa: WPS433,F401

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
