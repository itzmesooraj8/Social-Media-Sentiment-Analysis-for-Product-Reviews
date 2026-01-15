from pathlib import Path
import sys
from fastapi.testclient import TestClient

# Ensure project root is on sys.path so 'backend' package imports work
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
BACKEND_DIR = str(Path(__file__).resolve().parents[1] / 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.main import app
from auth.dependencies import get_current_user


def fake_user_dependency():
    return {"id": "test-user", "email": "test@example.com"}


def run_checks():
    app.dependency_overrides[get_current_user] = fake_user_dependency
    client = TestClient(app)

    # Create two test products and use their IDs for compare to avoid UUID issues
    prod_a = client.post('/api/products', json={"name":"Smoke A","sku":"SMOKE-A","category":"test"}).json()
    prod_b = client.post('/api/products', json={"name":"Smoke B","sku":"SMOKE-B","category":"test"}).json()
    id_a = prod_a.get('data', {}).get('id')
    id_b = prod_b.get('data', {}).get('id')

    endpoints = [
        ("GET", "/api/analytics"),
        ("GET", "/api/alerts"),
        ("GET", "/api/analytics/topics"),
        ("GET", f"/api/products/compare?id_a={id_a}&id_b={id_b}"),
        ("GET", "/api/dashboard"),
    ]

    results = {}
    for method, path in endpoints:
        resp = client.request(method, path)
        results[path] = {"status_code": resp.status_code, "json": None}
        try:
            results[path]["json"] = resp.json()
        except Exception:
            results[path]["text"] = resp.text

    for path, out in results.items():
        print(f"{path} -> {out['status_code']}")
        print(out.get("json") or out.get("text"))


if __name__ == "__main__":
    run_checks()
