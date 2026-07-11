from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

r1 = client.get("/publishing/wordpress/config")
print("CONFIG:", r1.status_code)
print(r1.text[:500])

r2 = client.post("/publishing/wordpress/test", json={"mode": "dry_run"})
print("TEST:", r2.status_code)
print(r2.text[:500])
