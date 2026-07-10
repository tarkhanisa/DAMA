from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA WordPress Flow Polish",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "WordPress flow polish smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-wordpress-flow-polish",
            "source_title": "تست جزئیات تلاش انتشار",
            "source_body": "این متن برای تست صفحه جزئیات تلاش انتشار وردپرس ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان تست جزئیات Draft",
            "variant_body": "متن آماده برای تست جزئیات Draft وردپرس.",
            "review_notes": "آماده تست flow polish.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    draft_response = client.post(
        f"/publishing/variants/{variant['id']}/wordpress/draft",
        json={
            "mode": "dry_run",
            "excerpt": "خلاصه تست جزئیات",
            "slug": "wordpress-flow-polish-test",
            "categories": [1],
            "tags": [2],
            "seo_title": "عنوان سئوی تست",
            "meta_description": "توضیح متای کوتاه برای تست جریان وردپرس.",
            "requested_by": "smoke-test",
        },
    )
    assert draft_response.status_code == 200, draft_response.text
    payload = draft_response.json()
    assert payload["attempt"]["status"] == "dry_run"
    assert payload["attempt"]["request_preview"]["seo_title"]
    assert payload["attempt"]["request_preview"]["meta_description"]

    attempt_id = payload["attempt"]["id"]

    detail_response = client.get(f"/publishing/attempts/{attempt_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["id"] == attempt_id
    assert detail["request_preview"]["seo_title"] == "عنوان سئوی تست"

    print("WordPress flow polish smoke test passed.")


if __name__ == "__main__":
    main()
