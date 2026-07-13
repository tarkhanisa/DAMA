from fastapi.testclient import TestClient

from src.main import app
from src.services.media_campaign_service import delete_media_campaign


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Campaign Smoke Telegram",
            "channel_type": "telegram",
            "target_url": "@damamedia_campaign_smoke",
            "notes": "Media campaign smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    create_response = client.post(
        "/publishing/campaigns",
        json={
            "project_name": "DAMA Smoke Project",
            "source_title": "کمپین تست چندرسانه‌ای",
            "source_body": "این متن مادر برای تست کمپین چندرسانه‌ای DAMA ساخته شده است.",
            "campaign_goal": "تست ساخت کمپین مادر",
            "media_urls": [
                "I:/DAMA/smoke-image.jpg",
                "I:/DAMA/smoke-video.mp4",
            ],
            "channel_ids": [channel["id"]],
            "notes": "smoke-test media campaign",
        },
    )
    assert create_response.status_code == 200, create_response.text
    campaign = create_response.json()

    assert campaign["id"]
    assert campaign["source_title"] == "کمپین تست چندرسانه‌ای"
    assert len(campaign["media_items"]) == 2
    assert campaign["media_items"][0]["type"] == "image"
    assert campaign["media_items"][1]["type"] == "video"
    assert campaign["channel_ids"] == [channel["id"]]

    get_response = client.get(f"/publishing/campaigns/{campaign['id']}")
    assert get_response.status_code == 200, get_response.text

    update_response = client.patch(
        f"/publishing/campaigns/{campaign['id']}",
        json={
            "status": "ready",
            "notes": "smoke-test updated",
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["status"] == "ready"

    list_response = client.get("/publishing/campaigns")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] >= 1

    delete_media_campaign(campaign["id"])

    print("Media campaign smoke test passed.")


if __name__ == "__main__":
    main()
