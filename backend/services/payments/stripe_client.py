# file: backend/services/payments/stripe_client.py

import os
from typing import Any

import stripe

from ...extensions import db
from ...models.order import Order
from ...models.payment import Payment


def _init_stripe():
    api_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not api_key:
        raise RuntimeError("STRIPE_SECRET_KEY не заданий")
    stripe.api_key = api_key


def create_checkout_session(order: Order, success_url: str, cancel_url: str) -> stripe.checkout.Session:
    """
    Створює Stripe Checkout Session для замовлення.
    """
    _init_stripe()

    # Simple: одна позиція – загальна сума
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[
            {
                "price_data": {
                    "currency": order.currency.lower(),
                    "product_data": {
                        "name": f"Order #{order.id}",
                    },
                    "unit_amount": int(order.total_amount * 100),
                },
                "quantity": 1,
            }
        ],
        metadata={
            "order_id": str(order.id),
        },
    )

    payment = Payment(
        order_id=order.id,
        provider="stripe",
        provider_session_id=session.id,
        amount=order.total_amount,
        currency=order.currency,
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    return session


def mark_payment_succeeded(session: dict[str, Any]) -> None:
    """
    Позначає платежі як успішні на основі webhook payload.
    """
    order_id = session.get("metadata", {}).get("order_id")
    if not order_id:
        return

    payment = Payment.query.filter_by(provider_session_id=session.get("id")).first()
    if not payment:
        return

    payment.status = "succeeded"
    payment.provider_payment_id = session.get("payment_intent")
    db.session.commit()
