from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    route_response = client.post(
        "/publishing/operator/session/route",
        json={"last_route": "/publishing"},
    )
    assert route_response.status_code == 200, route_response.text
    assert route_response.json()["last_route"] == "/publishing"

    session_response = client.get("/publishing/operator/session")
    assert session_response.status_code == 200, session_response.text
    assert session_response.json()["last_route"] == "/publishing"

    exit_response = client.post(
        "/publishing/operator/session/safe-exit",
        json={
            "last_route": "/produce/video",
            "backup": False,
            "shutdown": False,
        },
    )
    assert exit_response.status_code == 200, exit_response.text
    payload = exit_response.json()
    assert payload["ok"] is True
    assert payload["last_route"] == "/produce/video"

    print("Operator session smoke test passed.")


if __name__ == "__main__":
    main()
