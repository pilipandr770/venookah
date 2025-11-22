# file: test_webhook.py

import requests
import json

# Пример payload для payment_intent.succeeded
# Замени payment_intent_id на реальный из Stripe dashboard или логов

payment_intent_id = "pi_test_..."  # Замени на реальный

payload = {
    "id": "evt_test",
    "object": "event",
    "type": "payment_intent.succeeded",
    "data": {
        "object": {
            "id": payment_intent_id,
            "object": "payment_intent",
            "amount": 1000,
            "currency": "eur",
            "status": "succeeded",
            "metadata": {"order_id": "1"}
        }
    }
}

url = "http://127.0.0.1:5000/webhooks/stripe"

response = requests.post(url, json=payload)
print(response.status_code, response.text)