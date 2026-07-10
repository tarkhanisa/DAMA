from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA WordPress Draft Smoke",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "WordPress draft connector smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-wordpress-draft-content-asset",
            "source_title": "تست پیش‌نویس وردپرس",
            "source_body": "این متن برای تست ساخت پیش‌نویس وردپرس در حالت dry-run ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان آماده پیش‌نویس وردپرس",
            "variant_body": "متن آماده برای ساخت پیش‌نویس وردپرس.",
            "review_notes": "آماده تست dry-run وردپرس.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    draft_response = client.post(
        f"/publishing/variants/{variant['id']}/wordpress/draft",
        json={
            "mode": "dry_run",
            "requested_by": "smoke-test",
            "notes": "Dry-run connector test.",
        },
    )
    assert draft_response.status_code == 200, draft_response.text

    payload = draft_response.json()
    assert payload["ok"] is True
    assert payload["attempt"]["status"] == "dry_run"
    assert payload["attempt"]["connector"] == "wordpress"

    attempts_response = client.get("/publishing/attempts")
    assert attempts_response.status_code == 200, attempts_response.text
    assert attempts_response.json()["total"] >= 1

    print("WordPress draft connector smoke test passed.")


if __name__ == "__main__":
    main()
