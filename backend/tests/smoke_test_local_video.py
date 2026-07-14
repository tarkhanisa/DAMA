from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    config_response = client.get("/publishing/local-video/config")
    assert config_response.status_code == 200, config_response.text

    create_response = client.post(
        "/publishing/local-video/jobs",
        json={
            "project_name": "DAMA Smoke",
            "title": "تست ویدیو لوکال",
            "start_image": "I:/DAMA/smoke-start.png",
            "end_image": "I:/DAMA/smoke-end.png",
            "prompt": "حرکت آرام سینمایی از تصویر اول به تصویر دوم.",
            "duration_seconds": 4,
            "aspect_ratio": "16:9",
            "fps": 24,
        },
    )
    assert create_response.status_code == 200, create_response.text
    job = create_response.json()
    assert job["id"]
    assert job["duration_seconds"] == 4
    assert job["aspect_ratio"] == "16:9"

    run_response = client.post(
        f"/publishing/local-video/jobs/{job['id']}/run",
        json={"mode": "dry_run"},
    )
    assert run_response.status_code == 200, run_response.text
    payload = run_response.json()
    assert payload["ok"] is True
    assert payload["job"]["status"] == "dry_run"

    print("Local video smoke test passed.")


if __name__ == "__main__":
    main()
