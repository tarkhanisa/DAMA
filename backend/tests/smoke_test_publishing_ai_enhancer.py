from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA AI Enhancer Telegram",
            "channel_type": "telegram",
            "target_url": "@example",
            "notes": "AI enhancer smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-ai-content-asset",
            "source_title": "تست بهبود نسخه کانالی",
            "source_body": "این متن مادر برای بررسی بهبود نسخه کانالی با حالت dry run استفاده میشود.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    enhance_response = client.post(
        f"/publishing/variants/{variant['id']}/enhance",
        json={
            "mode": "dry_run",
            "instructions": "خروجی را کوتاه و خوانا کن.",
        },
    )
    assert enhance_response.status_code == 200, enhance_response.text

    payload = enhance_response.json()
    assert payload["ok"] is True
    assert payload["used_ai"] is False
    assert payload["variant"]["status"] == "ready_for_review"
    assert payload["variant"]["variant_body"]

    print("Publishing AI enhancer smoke test passed.")


if __name__ == "__main__":
    main()
