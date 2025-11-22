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
    current_app.logger.info("Received Stripe webhook")

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

    # Handle the event types we care about
    event_type = event.get("type")
    current_app.logger.info("Stripe event received: %s", event_type)

    if event_type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        handle_payment_intent_succeeded(payment_intent)
    elif event_type == "checkout.session.completed":
        session = event["data"]["object"]
        handle_checkout_session_completed(session)
    else:
        current_app.logger.info("Unhandled Stripe event type: %s", event_type)

    return jsonify({"status": "success"}), 200


def handle_checkout_session_completed(session):
    # Find the payment by session_id
    current_app.logger.info("handle_checkout_session_completed for session id=%s", session.get("id"))

    payment = Payment.query.filter_by(provider_session_id=session.get("id")).first()

    # Fallback: some sessions include a payment_intent id, try to find payment by that
    if not payment:
        pi = session.get("payment_intent") or session.get("payment")
        if pi:
            current_app.logger.info("No payment by session_id, trying payment_intent=%s", pi)
            payment = Payment.query.filter_by(provider_payment_id=pi).first()

    if not payment:
        current_app.logger.warning("No Payment record found for session: %s", session.get("id"))
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
    current_app.logger.info("handle_payment_intent_succeeded for intent id=%s", payment_intent.get("id"))

    payment = Payment.query.filter_by(provider_payment_id=payment_intent.get("id")).first()
    if not payment:
        current_app.logger.warning("No Payment record found for payment_intent: %s", payment_intent.get("id"))
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
