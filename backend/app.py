# file: backend/app.py

import logging
import os
import sys
import threading
import subprocess

from flask import Flask, jsonify
from dotenv import load_dotenv

from .config import get_config_class
from .extensions import init_extensions


def create_app() -> Flask:
    """
    Flask-Anwendungsfabrik für Venookah2.
    """
    # Lade .env (für lokale Entwicklung)
    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)

    config_name = os.getenv("APP_ENV", "development").lower()
    app.config.from_object(get_config_class(config_name))

    setup_logging(app)
    init_extensions(app)
    register_blueprints(app)

    # Start the Telegram bot as a background subprocess when the app starts.
    # Controlled via `START_TELEGRAM_BOT` env var (default: '1').
    # We guard against the Flask reloader starting the bot twice by checking
    # the `WERKZEUG_RUN_MAIN` environment variable — only start in the
    # reloader child (`'true'`) or when not using the reloader.
    def _maybe_start_telegram_bot():
        start_flag = os.getenv('START_TELEGRAM_BOT', '1').lower()
        if start_flag not in ('1', 'true', 'yes'):
            return

        # If the reloader is active, only start in the child process
        # where WERKZEUG_RUN_MAIN == 'true'. If the env var is not set,
        # proceed (useful for production servers).
        reload_flag = os.getenv('WERKZEUG_RUN_MAIN')
        if reload_flag is not None and reload_flag.lower() != 'true':
            return

        def _is_pid_running(pid: int) -> bool:
            try:
                if os.name == 'nt':
                    # On Windows, use tasklist to verify PID
                    res = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True)
                    return str(pid) in res.stdout
                else:
                    os.kill(pid, 0)
                    return True
            except Exception:
                return False

        pidfile = os.path.join(os.getenv('TEMP', '.'), 'telegram_bot.pid')
        if os.path.exists(pidfile):
            try:
                with open(pidfile, 'r', encoding='utf-8') as f:
                    existing_pid = int(f.read().strip())
                if _is_pid_running(existing_pid):
                    app.logger.info(f"Telegram bot already running (pid={existing_pid}), skipping start")
                    return
                else:
                    app.logger.info("Found stale telegram_bot.pid, will start a new bot")
            except Exception:
                # If anything goes wrong reading pidfile, proceed to start
                app.logger.exception("Error while checking existing telegram bot PID file")

        def _start():
            try:
                python = sys.executable or 'python'
                repo_root = os.path.dirname(os.path.dirname(__file__))
                # Run the bot as a module so relative imports work: `-m telegram_bot.bot`
                proc = subprocess.Popen([python, '-m', 'telegram_bot.bot'], cwd=repo_root)
                app.logger.info(f"Started telegram bot (pid={proc.pid})")
            except Exception:
                app.logger.exception("Failed to start telegram bot")

        t = threading.Thread(target=_start, name='telegram-bot-starter', daemon=True)
        t.start()

    _maybe_start_telegram_bot()

    @app.route("/health", methods=["GET"])
    def healthcheck():
        return jsonify({"status": "ok", "app": "venookah2"}), 200

    return app


def setup_logging(app: Flask) -> None:
    """Grundlegende Logging-Konfiguration."""
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(log_level)


def register_blueprints(app: Flask) -> None:
    """
    Registriere Blueprints.
    """
    from .blueprints.shop_public import bp as shop_public_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.shop_account import bp as shop_account_bp
    from .blueprints.warehouse import bp as warehouse_bp
    from .blueprints.webhooks import bp as webhooks_bp

    app.register_blueprint(shop_public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shop_account_bp)
    app.register_blueprint(warehouse_bp)
    app.register_blueprint(webhooks_bp)


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)

