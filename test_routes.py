"""Quick test to verify routes and endpoints."""
from app import app
from starlette.testclient import TestClient

client = TestClient(app)

# Test all endpoints
endpoints = [
    ("GET", "/api/settings"),
    ("GET", "/api/score?mode=test"),
    ("GET", "/api/history?mode=test"),
    ("POST", "/api/analyze", {"mode": "test", "dataset": "sample"}),
]

print("=== Route Registration ===")
for r in app.routes:
    path = getattr(r, "path", "?")
    methods = getattr(r, "methods", "mount")
    name = getattr(r, "name", "?")
    print(f"  {path} [{methods}] -> {name}")

print("\n=== Endpoint Tests ===")
for ep in endpoints:
    method = ep[0]
    url = ep[1]
    if method == "GET":
        r = client.get(url)
    else:
        r = client.post(url, json=ep[2])
    print(f"  {method} {url} => {r.status_code} {r.text[:80]}")
