# file: backend/ai/assistant_client.py

"""
Заглушка клієнта до OpenAI Assistants API.

Пізніше сюди можна підключити офіційний SDK.
"""

import os
from typing import Any


class AssistantClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.assistant_shop = os.getenv("OPENAI_ASSISTANT_ID_SHOP", "")
        self.assistant_boss = os.getenv("OPENAI_ASSISTANT_ID_BOSS", "")

    def ask_shop_assistant(self, message: str, context: dict | None = None) -> str:
        # TODO: інтеграція з OpenAI
        return f"[AI-продавець mock] {message}"

    def ask_boss_assistant(self, message: str, context: dict | None = None) -> str:
        # TODO: інтеграція з OpenAI
        return f"[AI-доповідь шефу mock] {message}"


assistant_client = AssistantClient()
