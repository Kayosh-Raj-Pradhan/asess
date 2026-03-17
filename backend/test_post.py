import json
import urllib.request

url = "http://localhost:8000/users/register"
body = {
    "full_name": "Test User",
    "username": "testuser123",
    "email": "test@example.com",
    "password": "Password123",
}

req = urllib.request.Request(
    url,
    data=json.dumps(body).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as r:
    print(r.status)
    print(r.read().decode())
