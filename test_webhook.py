# file: test_webhook.py

import requests
import json

# Beispiel-Payload für payment_intent.succeeded
# Ersetze `payment_intent_id` mit einem echten Wert aus dem Stripe-Dashboard oder den Logs

payment_intent_id = "pi_test_..."  # Ersetze mit echtem Wert

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