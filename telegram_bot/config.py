# file: telegram_bot/config.py

import os

from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000")
    OWNER_TELEGRAM_ID = int(os.getenv('OWNER_TELEGRAM_ID')) if os.getenv('OWNER_TELEGRAM_ID') else None


config = BotConfig()
