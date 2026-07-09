from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Variant WordPress",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "Variant smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-content-asset",
            "source_title": "عنوان تست انتشار",
            "source_body": "این یک متن مادر برای تست نسخهسازی کانالهای انتشار است. متن باید برای کانالهای مختلف قابل تبدیل باشد.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text

    plan = plan_response.json()
    assert plan["created"] == 1
    assert len(plan["items"]) == 1

    variant = plan["items"][0]
    assert variant["channel_type"] == "wordpress"
    assert variant["variant_body"]

    list_response = client.get("/publishing/variants")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] >= 1

    status_response = client.patch(
        f"/publishing/variants/{variant['id']}/status",
        json={"status": "ready_for_review"},
    )
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["status"] == "ready_for_review"

    print("Publishing variants smoke test passed.")


if __name__ == "__main__":
    main()
