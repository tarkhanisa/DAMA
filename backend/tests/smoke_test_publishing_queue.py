from fastapi.testclient import TestClient

from src.main import app
from src.services.runtime_cleanup_service import cleanup_test_runtime_data


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Queue Telegram Smoke",
            "channel_type": "telegram",
            "target_url": "@damamedia_queue_test",
            "notes": "Publishing queue smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-publishing-queue-content",
            "source_title": "تست صف انتشار",
            "source_body": "این متن برای تست صف انتشار DAMA ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان تست صف انتشار",
            "variant_body": "متن آماده برای dry-run صف انتشار تلگرام.",
            "review_notes": "آماده صف انتشار.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    queue_response = client.post(
        "/publishing/queue",
        json={
            "variant_id": variant["id"],
            "connector": "telegram",
            "mode": "dry_run",
            "requested_by": "smoke-test",
            "notes": "Publishing queue dry-run smoke.",
            "run_payload": {
                "chat_id": "@damamedia_queue_test",
            },
        },
    )
    assert queue_response.status_code == 200, queue_response.text
    queue_item = queue_response.json()["item"]
    assert queue_item["status"] == "queued"

    run_response = client.post(
        f"/publishing/queue/{queue_item['id']}/run",
        json={
            "mode": "dry_run",
            "requested_by": "smoke-test",
        },
    )
    assert run_response.status_code == 200, run_response.text
    run_payload = run_response.json()

    assert run_payload["ok"] is True
    assert run_payload["item"]["status"] == "dry_run_completed"
    assert run_payload["item"]["latest_attempt_id"]

    list_response = client.get("/publishing/queue")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] >= 1

    cleanup_result = cleanup_test_runtime_data(dry_run=False, backup=False)
    assert cleanup_result["ok"] is True

    print("Publishing queue smoke test passed.")


if __name__ == "__main__":
    main()
