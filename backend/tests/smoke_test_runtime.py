from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    response = client.get("/runtime/health")
    assert response.status_code == 200, response.text

    payload = response.json()

    assert "ok" in payload
    assert "status" in payload
    assert "backend" in payload
    assert "storage" in payload
    assert "ollama" in payload
    assert "config" in payload

    assert isinstance(payload["storage"], list)
    assert payload["backend"]["runtime"] == "fastapi"

    print("Runtime smoke test passed.")


if __name__ == "__main__":
    main()
