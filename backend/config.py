# file: backend/config.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _build_sqlalchemy_uri() -> str:
    """
    Формуємо SQLALCHEMY_DATABASE_URI.

    - Якщо є DATABASE_URL (наприклад, з Render), використовуємо його.
    - Якщо URL починається з postgres:// — замінюємо на postgresql+psycopg://
      (класична проблема Render/Heroku).
    - Інакше падаємо назад на локальний SQLite (для аварійного дев-режиму).
    """
    raw = os.getenv("DATABASE_URL")
    if raw:
        # Fix для формату postgres://
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql+psycopg://", 1)
        return raw

    # fallback — SQLite локально
    return f"sqlite:///{BASE_DIR / 'venookah2.db'}"


class BaseConfig:
    """Базовий конфіг для всіх середовищ."""

    # Загальне
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # БД
    SQLALCHEMY_DATABASE_URI = _build_sqlalchemy_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Схема бази (ДУЖЕ ВАЖЛИВО ДЛЯ ТЕБЕ)
    # Наприклад: venookah2, auction7, dating_bot тощо.
    DB_SCHEMA = os.getenv("DB_SCHEMA", "venookah2") if SQLALCHEMY_DATABASE_URI.startswith("postgresql") else None

    # Примушуємо Postgres використовувати потрібний search_path
    # (щоб усі таблиці створювались у твоїй схемі, а не в public)
    if SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                # це передається драйверу psycopg2
                "options": f"-csearch_path={DB_SCHEMA}"
            }
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    # Redis (для воркерів/черг, якщо треба)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # OpenAI / AI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ASSISTANT_ID_SHOP = os.getenv("OPENAI_ASSISTANT_ID_SHOP", "")
    OPENAI_ASSISTANT_ID_BOSS = os.getenv("OPENAI_ASSISTANT_ID_BOSS", "")

    # Telegram бот для шефа
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Мультимовність
    BABEL_DEFAULT_LOCALE = os.getenv("BABEL_DEFAULT_LOCALE", "de")
    BABEL_DEFAULT_TIMEZONE = os.getenv("BABEL_DEFAULT_TIMEZONE", "Europe/Berlin")

    # Безпека / CORS (можемо розширити пізніше)
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
    """Повертає клас конфіга по назві середовища."""
    env_name = (env_name or "").lower()
    if env_name == "production":
        return ProductionConfig
    if env_name == "testing":
        return TestingConfig
    return DevelopmentConfig
