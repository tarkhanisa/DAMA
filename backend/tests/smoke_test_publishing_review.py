from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Review WordPress",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "Review smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-review-content-asset",
            "source_title": "تست بازبینی انتشار",
            "source_body": "این متن مادر برای تست چرخه بازبینی نسخه انتشار ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "approved",
            "variant_title": "عنوان تأییدشده",
            "variant_body": "متن تأییدشده برای انتشار در مرحله بعد.",
            "review_notes": "بازبینی smoke test انجام شد.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    reviewed = review_response.json()
    assert reviewed["status"] == "approved"
    assert reviewed["variant_title"] == "عنوان تأییدشده"
    assert reviewed["review_notes"]
    assert isinstance(reviewed["review_history"], list)

    print("Publishing review smoke test passed.")


if __name__ == "__main__":
    main()
