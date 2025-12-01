#!/usr/bin/env python
"""Test script for /api/ai/owner_query endpoint"""

import requests

# Test 1: Warehouse query
print("=== Test 1: Warehouse Query ===")
response = requests.post(
    'http://127.0.0.1:5000/api/ai/owner_query',
    data={
        'message': 'Was haben wir am Lager?',
        'department': 'warehouse'
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test 2: Shop query
print("=== Test 2: Shop Query ===")
response = requests.post(
    'http://127.0.0.1:5000/api/ai/owner_query',
    data={
        'message': 'Wie viele Bestellungen haben wir diese Woche?',
        'department': 'shop'
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test 3: Sea freight query
print("=== Test 3: Sea Freight Query ===")
response = requests.post(
    'http://127.0.0.1:5000/api/ai/owner_query',
    data={
        'message': 'Welche Sendungen sind unterwegs?',
        'department': 'sea'
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
