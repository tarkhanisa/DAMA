from datetime import datetime
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

now = datetime.now().strftime("%Y%m%d-%H%M%S")

print("Checking WordPress config...")
config_response = client.get("/publishing/wordpress/config")
print("CONFIG:", config_response.status_code, config_response.text[:500])

print("\nTesting real WordPress authentication...")
test_response = client.post(
    "/publishing/wordpress/test",
    json={"mode": "wordpress"},
)
print("AUTH TEST:", test_response.status_code, test_response.text[:800])

test_payload = test_response.json()

if not test_payload.get("ok"):
    raise SystemExit("WordPress real authentication failed. Fix backend/.env.local or Application Password first.")

print("\nCreating WordPress publishing channel...")
channel_response = client.post(
    "/publishing/channels",
    json={
        "name": "Damamedia Local WordPress",
        "channel_type": "wordpress",
        "target_url": "http://damamedia.local",
        "notes": "Local WordPress draft test channel.",
    },
)
print("CHANNEL:", channel_response.status_code, channel_response.text[:500])
channel = channel_response.json()

print("\nCreating publishing variant...")
plan_response = client.post(
    "/publishing/variants/plan",
    json={
        "content_asset_id": f"local-wordpress-draft-test-{now}",
        "source_title": "تست اتصال DAMA به وردپرس لوکال",
        "source_body": (
            "این یک متن آزمایشی است که توسط DAMA برای بررسی اتصال واقعی به وردپرس لوکال دامامدیا ساخته شده است. "
            "این نوشته نباید منتشر شود و فقط باید به صورت پیش‌نویس در وردپرس ثبت شود."
        ),
        "channel_ids": [channel["id"]],
    },
)
print("PLAN:", plan_response.status_code, plan_response.text[:800])
variant = plan_response.json()["items"][0]

print("\nReviewing variant as ready_for_publish...")
review_response = client.patch(
    f"/publishing/variants/{variant['id']}/review",
    json={
        "status": "ready_for_publish",
        "variant_title": f"تست پیش‌نویس وردپرس از DAMA - {now}",
        "variant_body": (
            "<p>این نوشته یک تست واقعی از اتصال DAMA به وردپرس لوکال دامامدیا است.</p>"
            "<p>وضعیت این نوشته باید فقط <strong>Draft / پیش‌نویس</strong> باشد و نباید منتشر شود.</p>"
            "<p>اگر این متن را در بخش نوشته‌های وردپرس می‌بینی، یعنی اتصال DAMA به وردپرس درست کار می‌کند.</p>"
        ),
        "review_notes": "آماده ساخت Draft واقعی روی وردپرس لوکال.",
        "reviewed_by": "DAMA local test script",
    },
)
print("REVIEW:", review_response.status_code, review_response.text[:500])

print("\nCreating real WordPress draft...")
draft_response = client.post(
    f"/publishing/variants/{variant['id']}/wordpress/draft",
    json={
        "mode": "wordpress",
        "excerpt": "تست اتصال DAMA به وردپرس لوکال",
        "slug": f"dama-local-draft-test-{now}",
        "categories": [],
        "tags": [],
        "seo_title": "تست اتصال DAMA به وردپرس لوکال",
        "meta_description": "این نوشته برای تست ساخت پیش‌نویس وردپرس توسط DAMA ایجاد شده است.",
        "requested_by": "DAMA local test script",
        "notes": "First real local WordPress draft test.",
    },
)
print("DRAFT:", draft_response.status_code, draft_response.text[:1500])

payload = draft_response.json()
attempt = payload.get("attempt", {})
response = attempt.get("response", {})

print("\nRESULT")
print("Attempt ID:", attempt.get("id"))
print("Status:", attempt.get("status"))
print("WordPress Post ID:", response.get("wordpress_post_id"))
print("WordPress Link:", response.get("wordpress_link"))
print("Error:", attempt.get("error"))
