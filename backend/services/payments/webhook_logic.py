# file: backend/services/payments/webhook_logic.py

from typing import Any

from .stripe_client import mark_payment_succeeded


def handle_stripe_event(event: dict[str, Any]) -> None:
    """
    Verarbeitung von Stripe-Webhook-Ereignissen.
    MVP: nur payment_intent.succeeded über checkout.session.completed.
    """
    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        mark_payment_succeeded(data_object)
