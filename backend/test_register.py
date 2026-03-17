import json
import urllib.request
import sys

url = "http://localhost:8000/users/register"
body = {
    "full_name": "Alice Test",
    "username": "alicedemo",
    "email": "alice@example.com",
    "password": "SecurePass123",
}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        print(f"Status: {r.status}")
        response_body = json.loads(r.read().decode())
        print(json.dumps(response_body, indent=2))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
