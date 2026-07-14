from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    status_response = client.get("/publishing/local-tools/status")
    assert status_response.status_code == 200, status_response.text
    status = status_response.json()
    assert "ollama" in status
    assert "comfyui" in status
    assert "local_video_command" in status

    enhance_response = client.post(
        "/publishing/local-video/prompt/enhance",
        json={
            "dry_run": True,
            "project_name": "DAMA Smoke",
            "title": "ویدیوی تست",
            "prompt": "حرکت آرام دوربین از روی تصویر شروع.",
            "duration_seconds": 4,
            "aspect_ratio": "16:9",
        },
    )
    assert enhance_response.status_code == 200, enhance_response.text
    payload = enhance_response.json()
    assert payload["ok"] is True
    assert payload["enhanced_prompt"]
    assert payload["negative_prompt"]

    print("Local AI tools smoke test passed.")


if __name__ == "__main__":
    main()
