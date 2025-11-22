# file: backend/ai/shop_assistant.py

"""
Логіка ІІ-продавця для магазину.
"""

from ..models.product import Product
from .assistant_client import assistant_client


def generate_product_answer(product: Product, user_question: str) -> str:
    """
    Формує запит до AI-продавця з контекстом про товар.
    (Поки що mock через AssistantClient).
    """
    context = {
        "product_name": product.name,
        "description": product.description,
        "price_b2c": float(product.price_b2c or 0),
        "price_b2b": float(product.price_b2b or 0),
    }
    return assistant_client.ask_shop_assistant(user_question, context=context)
