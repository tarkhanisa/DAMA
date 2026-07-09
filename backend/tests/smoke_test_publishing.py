from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    create_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Manual Review Channel",
            "channel_type": "manual",
            "target_url": "local-review",
            "notes": "Smoke test channel.",
        },
    )
    assert create_response.status_code == 200, create_response.text

    channel = create_response.json()
    assert channel["id"]
    assert channel["channel_type"] == "manual"

    list_response = client.get("/publishing/channels")
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()
    assert "items" in payload
    assert payload["total"] >= 1

    test_response = client.post(f"/publishing/channels/{channel['id']}/test")
    assert test_response.status_code == 200, test_response.text
    test_payload = test_response.json()
    assert test_payload["status"] in {"ready", "configured", "not_configured", "needs_review"}

    print("Publishing smoke test passed.")


if __name__ == "__main__":
    main()
