# file: backend/config.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _build_sqlalchemy_uri() -> str:
    """Erstelle die SQLALCHEMY_DATABASE_URI.

    - Wenn `DATABASE_URL` gesetzt ist (z. B. von Render), verwenden wir sie.
    - Wenn die URL mit `postgres://` beginnt, ersetzen wir sie durch
      `postgresql+psycopg2://` (häufiges Render/Heroku-Problem).
    - Andernfalls verwenden wir lokal SQLite als Fallback (für schnellen Dev-Use).
    """
    raw = os.getenv("DATABASE_URL")
    if raw:
        # Fix für das Format postgres://
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql+psycopg2://", 1)
        return raw

    # Fallback — lokal SQLite
    return f"sqlite:///{BASE_DIR / 'venookah2.db'}"


class BaseConfig:
    """Basis-Konfiguration für alle Umgebungen."""

    # Allgemein
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Datenbank
    SQLALCHEMY_DATABASE_URI = _build_sqlalchemy_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def get_table_args():
    """Return table_args for models - schema only for PostgreSQL."""
    if _build_sqlalchemy_uri().startswith("postgresql"):
        return {'schema': os.getenv("DB_SCHEMA", "venookah2")}
    return {}

    # Erzwinge, dass Postgres den gewünschten search_path verwendet
    # (damit alle Tabellen in deinem Schema und nicht in "public" erstellt werden)
    if SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                # dies wird an den psycopg2-Treiber übergeben
                "options": f"-csearch_path={DB_SCHEMA}"
            }
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    # Redis (für Worker/Queues, falls benötigt)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # OpenAI / AI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ASSISTANT_ID_SHOP = os.getenv("OPENAI_ASSISTANT_ID_SHOP", "")
    OPENAI_ASSISTANT_ID_BOSS = os.getenv("OPENAI_ASSISTANT_ID_BOSS", "")

    # Telegram-Bot für den Inhaber
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Mehrsprachigkeit
    BABEL_DEFAULT_LOCALE = os.getenv("BABEL_DEFAULT_LOCALE", "de")
    BABEL_DEFAULT_TIMEZONE = os.getenv("BABEL_DEFAULT_TIMEZONE", "Europe/Berlin")
    # Unterstützte Sprachen (Reihenfolge wichtig für best_match)
    SUPPORTED_LANGUAGES = ["de", "en"]

    # Sicherheit / CORS (kann später erweitert werden)
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")

    # Shipping APIs
    DHL_API_KEY = os.getenv("DHL_API_KEY", "")
    DHL_BASE_URL = os.getenv("DHL_BASE_URL", "https://api.dhl.com")

    DPD_DELIS_ID = os.getenv("DPD_DELIS_ID", "sandboxdpd")
    DPD_PASSWORD = os.getenv("DPD_PASSWORD", "xMmshh1")
    DPD_MESSAGE_LANGUAGE = os.getenv("DPD_MESSAGE_LANGUAGE", "de_DE")
    DPD_BASE_URL = os.getenv("DPD_BASE_URL", "https://public-ws-stage.dpd.com")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"


class TestingConfig(BaseConfig):
    TESTING = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def get_config_class(env_name: str):
    """Gibt die Konfigurationsklasse für den angegebenen Umgebungsnamen zurück."""
    env_name = (env_name or "").lower()
    if env_name == "production":
        return ProductionConfig
    if env_name == "testing":
        return TestingConfig
    return DevelopmentConfig
