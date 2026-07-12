from datetime import datetime
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

now = datetime.now().strftime("%Y%m%d-%H%M%S")

print("Checking Telegram config...")
config_response = client.get("/publishing/telegram/config")
print("CONFIG:", config_response.status_code, config_response.text[:800])

config = config_response.json()

if not config.get("ready"):
    raise SystemExit("Telegram config is not ready. Check DAMA_TELEGRAM_BOT_TOKEN in backend/.env.local")

print("\nTesting real Telegram bot...")
test_response = client.post(
    "/publishing/telegram/test",
    json={"mode": "telegram"},
)
print("BOT TEST:", test_response.status_code, test_response.text[:1200])

test_payload = test_response.json()

if not test_payload.get("ok"):
    raise SystemExit("Telegram real bot test failed.")

print("\nCreating Telegram publishing channel...")
channel_response = client.post(
    "/publishing/channels",
    json={
        "name": "DAMA Telegram Real Test",
        "channel_type": "telegram",
        "target_url": config.get("default_chat_id_preview") or "",
        "notes": "Real Telegram test channel.",
    },
)
print("CHANNEL:", channel_response.status_code, channel_response.text[:500])
channel = channel_response.json()

print("\nCreating Telegram variant...")
plan_response = client.post(
    "/publishing/variants/plan",
    json={
        "content_asset_id": f"telegram-real-test-{now}",
        "source_title": "تست ارسال واقعی تلگرام از DAMA",
        "source_body": (
            "این یک پیام تست واقعی از DAMA است. "
            "هدف فقط بررسی اتصال Bot تلگرام، ساخت نسخه کانالی و ثبت گزارش ارسال است."
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
        "variant_title": f"تست تلگرام DAMA - {now}",
        "variant_body": (
            "تست ارسال واقعی از DAMA به تلگرام\n\n"
            "اگر این پیام را در کانال/گروه تست می‌بینی، یعنی اتصال Telegram Bot به DAMA درست کار می‌کند.\n\n"
            "این پیام فقط برای تست فنی است."
        ),
        "review_notes": "آماده ارسال تست واقعی تلگرام.",
        "reviewed_by": "DAMA local test script",
    },
)
print("REVIEW:", review_response.status_code, review_response.text[:500])

print("\nPreviewing Telegram message...")
preview_response = client.post(
    f"/publishing/variants/{variant['id']}/telegram/preview",
    json={},
)
print("PREVIEW:", preview_response.status_code, preview_response.text[:1000])

print("\nSending real Telegram test message...")
send_response = client.post(
    f"/publishing/variants/{variant['id']}/telegram/send-test",
    json={
        "mode": "telegram",
        "requested_by": "DAMA local test script",
        "notes": "First real Telegram test send.",
        "disable_web_page_preview": True,
    },
)
print("SEND:", send_response.status_code, send_response.text[:1500])

payload = send_response.json()
attempt = payload.get("attempt", {})
response = attempt.get("response", {})

print("\nRESULT")
print("Attempt ID:", attempt.get("id"))
print("Status:", attempt.get("status"))
print("Telegram Message ID:", response.get("telegram_message_id"))
print("Error:", attempt.get("error"))
