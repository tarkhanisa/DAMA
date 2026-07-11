from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    config_response = client.get("/publishing/telegram/config")
    assert config_response.status_code == 200, config_response.text
    assert "bot_token_configured" in config_response.json()

    test_response = client.post(
        "/publishing/telegram/test",
        json={"mode": "dry_run"},
    )
    assert test_response.status_code == 200, test_response.text
    assert test_response.json()["ok"] is True

    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Telegram Smoke",
            "channel_type": "telegram",
            "target_url": "@damamedia_test",
            "notes": "Telegram connector smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-telegram-content-asset",
            "source_title": "تست تلگرام DAMA",
            "source_body": "این متن برای تست پیش‌نمایش و dry-run تلگرام ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان تست تلگرام",
            "variant_body": "متن آماده برای تست dry-run تلگرام.",
            "review_notes": "آماده تست تلگرام.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    preview_response = client.post(
        f"/publishing/variants/{variant['id']}/telegram/preview",
        json={"chat_id": "@damamedia_test"},
    )
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    assert preview["ok"] is True
    assert preview["text"]

    send_response = client.post(
        f"/publishing/variants/{variant['id']}/telegram/send-test",
        json={
            "mode": "dry_run",
            "chat_id": "@damamedia_test",
            "requested_by": "smoke-test",
            "notes": "Telegram dry-run smoke.",
        },
    )
    assert send_response.status_code == 200, send_response.text
    payload = send_response.json()
    assert payload["ok"] is True
    assert payload["attempt"]["status"] == "dry_run"
    assert payload["attempt"]["connector"] == "telegram"

    print("Telegram connector smoke test passed.")


if __name__ == "__main__":
    main()
