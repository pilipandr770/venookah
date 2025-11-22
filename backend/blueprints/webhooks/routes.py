# file: backend/blueprints/webhooks/routes.py

import json
import stripe
from flask import Blueprint, request, jsonify, current_app

from ...extensions import db
from ...models.payment import Payment
from ...models.order import Order, OrderStatus
from ...services.prepare_shipment import prepare_shipment

bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@bp.route("/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("stripe-signature")

    try:
        if current_app.config.get("APP_ENV") == "development":
            # Для локального тесту без підпису
            event = json.loads(payload)
        else:
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config["STRIPE_WEBHOOK_SECRET"]
            )
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"error": "Invalid signature"}), 400

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        handle_payment_intent_succeeded(payment_intent)
    else:
        print(f"Unhandled event type {event['type']}")

    return jsonify({"status": "success"}), 200


def handle_checkout_session_completed(session):
    # Find the payment by session_id
    payment = Payment.query.filter_by(provider_session_id=session["id"]).first()
    if not payment:
        return

    # Update payment status
    payment.status = "completed"
    payment.raw_payload = session
    db.session.commit()

    # Update order status
    order = payment.order
    order.status = OrderStatus.PAID
    db.session.commit()

    # Prepare shipment
    prepare_shipment(order.id)


def handle_payment_intent_succeeded(payment_intent):
    # Find the payment by payment_intent id
    payment = Payment.query.filter_by(provider_payment_id=payment_intent["id"]).first()
    if not payment:
        return

    # Update payment status
    payment.status = "completed"
    payment.raw_payload = payment_intent
    db.session.commit()

    # Update order status
    order = payment.order
    order.status = OrderStatus.PAID
    db.session.commit()

    # Prepare shipment
    prepare_shipment(order.id)
