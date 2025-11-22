# file: backend/app.py

import logging
import os

from flask import Flask, jsonify
from dotenv import load_dotenv

from .config import get_config_class
from .extensions import init_extensions


def create_app() -> Flask:
    """
    Фабрика Flask-додатку для Venookah2.
    """
    # Завантажуємо .env (для локальної розробки)
    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)

    config_name = os.getenv("APP_ENV", "development").lower()
    app.config.from_object(get_config_class(config_name))

    setup_logging(app)
    init_extensions(app)
    register_blueprints(app)

    @app.route("/health", methods=["GET"])
    def healthcheck():
        return jsonify({"status": "ok", "app": "venookah2"}), 200

    return app


def setup_logging(app: Flask) -> None:
    """Налаштування базового логування."""
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(log_level)


def register_blueprints(app: Flask) -> None:
    """
    Реєструємо blueprints.
    """
    from .blueprints.shop_public import bp as shop_public_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.shop_account import bp as shop_account_bp
    from .blueprints.warehouse import bp as warehouse_bp

    app.register_blueprint(shop_public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shop_account_bp)
    app.register_blueprint(warehouse_bp)


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)

