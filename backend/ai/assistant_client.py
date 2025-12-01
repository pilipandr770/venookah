# file: backend/ai/assistant_client.py

"""
Simple OpenAI client wrapper for shop assistant.

Note: Boss assistant queries are handled via /api/ai/owner_query endpoint
which uses Chat Completions API directly with database snapshots.
"""

import os
from typing import Any


class AssistantClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.assistant_shop = os.getenv("OPENAI_ASSISTANT_ID_SHOP", "")
        self.assistant_boss = os.getenv("OPENAI_ASSISTANT_ID_BOSS", "")

    def ask_shop_assistant(self, message: str, context: dict | None = None) -> str:
        # Shop assistant for product queries
        # For now returns mock, can be extended to use Chat Completions API
        return f"[AI-продавець mock] {message}"

    def ask_boss_assistant(self, message: str, context: dict | None = None) -> str:
        # Boss assistant is handled via /api/ai/owner_query endpoint in shop_public routes
        # This method is kept for compatibility but should not be used directly
        return f"[Use /api/ai/owner_query endpoint instead] {message}"


assistant_client = AssistantClient()
