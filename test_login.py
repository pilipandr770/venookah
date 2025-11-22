import requests

# Test login
url = 'http://127.0.0.1:5000/login'
data = {
    'email': 'owner@example.com',
    'password': 'ChangeMe123!'
}

response = requests.post(url, data=data, allow_redirects=False)

print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
if response.status_code == 302:
    print("Login successful, redirect to:", response.headers.get('Location'))
elif response.status_code == 200:
    print("Login failed, check form")
    print("Response text:", response.text[:500])
else:
    print("Error:", response.status_code)
    print("Response text:", response.text[:500])