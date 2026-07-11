from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


def patch_backend_check() -> None:
    target = ROOT / "scripts/backend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "smoke_test_telegram_connector.py" in text:
        print("Skipped backend-check patch.")
        return

    text = text.rstrip() + r'''

$TelegramConnectorSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_telegram_connector.py"
$TelegramConnectorPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $TelegramConnectorSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_telegram_connector.py..."
    & $TelegramConnectorPython $TelegramConnectorSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_telegram_connector.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\publishing\\telegram\\page.tsx",',
        '".\\frontend\\src\\components\\telegram-connection-test-action.tsx",',
        '".\\frontend\\src\\components\\telegram-preview-test-send-action.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\publishing\\wordpress\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Telegram page does not call config endpoint." not in text:
        block = r'''
$TelegramPage = Read-TextFile ".\frontend\src\app\publishing\telegram\page.tsx"
$TelegramTestAction = Read-TextFile ".\frontend\src\components\telegram-connection-test-action.tsx"
$TelegramVariantAction = Read-TextFile ".\frontend\src\components\telegram-preview-test-send-action.tsx"

if ($TelegramPage -notmatch "/publishing/telegram/config") {
    throw "Telegram page does not call config endpoint."
}

if ($TelegramTestAction -notmatch "/publishing/telegram/test") {
    throw "Telegram connection test action does not call test endpoint."
}

if ($TelegramVariantAction -notmatch "/telegram/preview") {
    throw "Telegram variant action is missing preview endpoint."
}

if ($TelegramVariantAction -notmatch "/telegram/send-test") {
    throw "Telegram variant action is missing send-test endpoint."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "backend/src/services/telegram_connector_service.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4
import json
import os

from src.services.publishing_channel_service import get_channel
from src.services.publishing_variant_service import get_variant, read_variants, write_variants


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
ATTEMPTS_PATH = DATA_DIR / "publishing_attempts.json"

TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_SAFE_PREVIEW_LENGTH = 3900


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not ATTEMPTS_PATH.exists():
        ATTEMPTS_PATH.write_text("[]\n", encoding="utf-8")


def read_attempts() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(ATTEMPTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_attempts(attempts: list[dict[str, Any]]) -> None:
    ensure_store()
    ATTEMPTS_PATH.write_text(
        json.dumps(attempts, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def telegram_config_status() -> dict[str, Any]:
    token = os.getenv("DAMA_TELEGRAM_BOT_TOKEN", "").strip()
    default_chat_id = os.getenv("DAMA_TELEGRAM_DEFAULT_CHAT_ID", "").strip()

    missing = []

    if not token:
        missing.append("DAMA_TELEGRAM_BOT_TOKEN")

    return {
        "ready": len(missing) == 0,
        "missing": missing,
        "bot_token_configured": bool(token),
        "default_chat_id_configured": bool(default_chat_id),
        "default_chat_id_preview": default_chat_id,
        "secrets_redacted": True,
        "message": "Telegram config is complete." if not missing else "Telegram config is incomplete.",
    }


def telegram_token() -> str:
    token = os.getenv("DAMA_TELEGRAM_BOT_TOKEN", "").strip()

    if not token:
        raise RuntimeError("Telegram env is incomplete. Missing: DAMA_TELEGRAM_BOT_TOKEN")

    return token


def normalize_chat_id(value: str) -> str:
    chat_id = value.strip()

    if not chat_id:
        return ""

    prefixes = [
        "https://t.me/",
        "http://t.me/",
        "t.me/",
    ]

    for prefix in prefixes:
        if chat_id.startswith(prefix):
            chat_id = chat_id[len(prefix):].strip("/")

    if chat_id and not chat_id.startswith("@") and not chat_id.lstrip("-").isdigit():
        chat_id = "@" + chat_id

    return chat_id


def resolve_chat_id(payload: dict[str, Any], channel: dict[str, Any] | None) -> str:
    explicit = normalize_chat_id(str(payload.get("chat_id") or ""))

    if explicit:
        return explicit

    env_chat_id = normalize_chat_id(os.getenv("DAMA_TELEGRAM_DEFAULT_CHAT_ID", ""))

    if env_chat_id:
        return env_chat_id

    if channel:
        return normalize_chat_id(str(channel.get("target_url") or ""))

    return ""


def format_connector_exception(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, HTTPError):
        body = ""

        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""

        parsed: Any = None
        message = str(exc)

        if body:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    message = str(parsed.get("description") or parsed.get("message") or parsed.get("error_code") or message)
            except json.JSONDecodeError:
                parsed = body[:1200]

        return {
            "type": "HTTPError",
            "status_code": exc.code,
            "reason": exc.reason,
            "message": message,
            "body_preview": parsed,
        }

    if isinstance(exc, URLError):
        return {
            "type": "URLError",
            "message": str(exc.reason),
        }

    return {
        "type": exc.__class__.__name__,
        "message": str(exc),
    }


def telegram_api_request(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    token = telegram_token()
    url = f"https://api.telegram.org/bot{token}/{method}"

    data = json.dumps(payload or {}).encode("utf-8")

    request = Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=45) as response:
        raw = response.read().decode("utf-8")
        result = json.loads(raw) if raw else {}

    return result if isinstance(result, dict) else {"result": result}


def test_telegram_connection(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode") or "dry_run").strip().lower()
    config = telegram_config_status()

    if mode == "dry_run":
        return {
            "ok": True,
            "mode": mode,
            "ready_for_real_test": config["ready"],
            "config": config,
            "message": "Dry-run completed. No request was sent to Telegram.",
        }

    if mode != "telegram":
        return {
            "ok": False,
            "mode": mode,
            "config": config,
            "message": f"Unsupported Telegram test mode: {mode}",
        }

    if not config["ready"]:
        return {
            "ok": False,
            "mode": mode,
            "config": config,
            "message": "Telegram config is incomplete.",
        }

    try:
        data = telegram_api_request("getMe")
        bot = data.get("result") if isinstance(data.get("result"), dict) else {}

        return {
            "ok": bool(data.get("ok")),
            "mode": mode,
            "config": config,
            "bot": {
                "id": bot.get("id"),
                "username": bot.get("username"),
                "first_name": bot.get("first_name"),
            },
            "message": "Telegram bot authentication test succeeded." if data.get("ok") else "Telegram bot authentication test failed.",
            "raw": data,
        }
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError, RuntimeError) as exc:
        detail = format_connector_exception(exc)

        return {
            "ok": False,
            "mode": mode,
            "config": config,
            "error_detail": detail,
            "message": detail.get("message", str(exc)),
        }


def build_telegram_text(variant: dict[str, Any]) -> str:
    title = str(variant.get("variant_title") or "").strip()
    body = str(variant.get("variant_body") or "").strip()

    if title and not body.startswith(title):
        text = f"{title}\n\n{body}".strip()
    else:
        text = body or title

    text = text.replace("<p>", "").replace("</p>", "\n\n")
    text = text.replace("<strong>", "*").replace("</strong>", "*")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = "\n\n".join(part.strip() for part in text.split("\n\n") if part.strip())

    if len(text) > TELEGRAM_SAFE_PREVIEW_LENGTH:
        text = text[:TELEGRAM_SAFE_PREVIEW_LENGTH].rstrip() + "\n\n"

    return text


def preview_telegram_variant(variant_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    variant = get_variant(variant_id)

    if not variant:
        return None

    payload = payload or {}
    channel = get_channel(str(variant.get("channel_id") or ""))
    chat_id = resolve_chat_id(payload, channel)
    text = build_telegram_text(variant)

    issues: list[str] = []
    warnings: list[str] = []

    if str(variant.get("channel_type") or "") != "telegram":
        issues.append("این نسخه برای کانال تلگرام نیست.")

    if not text:
        issues.append("متن نسخه خالی است.")

    if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
        issues.append("متن برای پیام تلگرام بیش از حد طولانی است.")

    if not chat_id:
        warnings.append("chat_id مشخص نشده است. برای ارسال واقعی باید chat_id یا target_url کانال مشخص باشد.")

    if not telegram_config_status()["ready"]:
        warnings.append("Bot Token تلگرام در env تنظیم نشده است؛ فقط dry-run قابل اتکاست.")

    return {
        "ok": len(issues) == 0,
        "can_dry_run": len(issues) == 0,
        "can_send_real_test": len(issues) == 0 and telegram_config_status()["ready"] and bool(chat_id),
        "issues": issues,
        "warnings": warnings,
        "chat_id_preview": chat_id,
        "message_length": len(text),
        "text": text,
        "variant": {
            "id": variant.get("id"),
            "title": variant.get("variant_title"),
            "status": variant.get("status"),
            "channel_type": variant.get("channel_type"),
            "channel_name": variant.get("channel_name"),
        },
    }


def update_variant_after_attempt(variant_id: str, attempt: dict[str, Any]) -> None:
    variants = read_variants()

    for index, variant in enumerate(variants):
        if variant.get("id") != variant_id:
            continue

        updated = dict(variant)
        updated["latest_publish_attempt_id"] = attempt.get("id")
        updated["latest_publish_attempt_status"] = attempt.get("status")
        updated["latest_publish_attempt_at"] = attempt.get("created_at")
        updated["updated_at"] = utc_now()

        variants[index] = updated
        write_variants(variants)
        return


def send_telegram_test_from_variant(
    variant_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    variant = get_variant(variant_id)

    if not variant:
        return None

    channel = get_channel(str(variant.get("channel_id") or ""))
    mode = str(payload.get("mode") or "dry_run").strip().lower()
    requested_by = str(payload.get("requested_by") or "operator").strip()
    notes = str(payload.get("notes") or "").strip()
    chat_id = resolve_chat_id(payload, channel)
    preview = preview_telegram_variant(variant_id, payload)

    attempt_id = str(uuid4())
    now = utc_now()

    attempt: dict[str, Any] = {
        "id": attempt_id,
        "variant_id": variant_id,
        "content_asset_id": variant.get("content_asset_id"),
        "channel_id": variant.get("channel_id"),
        "channel_name": variant.get("channel_name"),
        "channel_type": variant.get("channel_type"),
        "connector": "telegram",
        "mode": mode,
        "requested_by": requested_by,
        "notes": notes,
        "status": "created",
        "created_at": now,
        "updated_at": now,
        "target_url": channel.get("target_url") if channel else "",
        "variant_status_at_attempt": variant.get("status"),
        "safe_config": telegram_config_status(),
        "validation": preview,
        "request_preview": {
            "chat_id": chat_id,
            "text_preview": preview.get("text", "")[:1000] if preview else "",
            "disable_web_page_preview": bool(payload.get("disable_web_page_preview", True)),
        },
        "response": {},
        "error": "",
        "error_detail": {},
    }

    if not preview or not preview["ok"]:
        attempt["status"] = "blocked"
        attempt["error"] = "Telegram preview validation failed."
    elif mode == "dry_run":
        attempt["status"] = "dry_run"
        attempt["response"] = {
            "message": "Dry-run only. No Telegram request was sent.",
            "would_send": attempt["request_preview"],
        }
    elif mode == "telegram":
        if not preview["can_send_real_test"]:
            attempt["status"] = "blocked"
            attempt["error"] = "Telegram config or chat_id is incomplete."
        else:
            try:
                data = telegram_api_request(
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": preview["text"],
                        "disable_web_page_preview": bool(payload.get("disable_web_page_preview", True)),
                    },
                )
                result = data.get("result") if isinstance(data.get("result"), dict) else {}
                attempt["status"] = "test_sent" if data.get("ok") else "failed"
                attempt["response"] = {
                    "telegram_ok": data.get("ok"),
                    "telegram_message_id": result.get("message_id"),
                    "chat": result.get("chat"),
                    "raw": data,
                }
                if not data.get("ok"):
                    attempt["error"] = str(data)
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError, RuntimeError) as exc:
                detail = format_connector_exception(exc)
                attempt["status"] = "failed"
                attempt["error"] = str(detail.get("message") or exc)
                attempt["error_detail"] = detail
    else:
        attempt["status"] = "blocked"
        attempt["error"] = f"Unsupported mode: {mode}"

    attempt["updated_at"] = utc_now()

    attempts = read_attempts()
    attempts.insert(0, attempt)
    write_attempts(attempts)

    update_variant_after_attempt(variant_id, attempt)

    return {
        "ok": attempt["status"] in {"dry_run", "test_sent"},
        "attempt": attempt,
        "message": attempt.get("error") or attempt["status"],
    }
    ''',
)


# Patch publishing API with Telegram routes.
api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "telegram_connector_service" not in api:
    telegram_import = r'''
from src.services.telegram_connector_service import (
    preview_telegram_variant,
    send_telegram_test_from_variant,
    telegram_config_status,
    test_telegram_connection,
)
'''.strip()

    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\n" + telegram_import + "\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/telegram/config")' not in api:
    api += r'''


@router.get("/telegram/config")
def api_telegram_config() -> dict[str, Any]:
    return telegram_config_status()


@router.post("/telegram/test")
def api_telegram_test(payload: dict[str, Any]) -> dict[str, Any]:
    return test_telegram_connection(payload)


@router.post("/variants/{variant_id}/telegram/preview")
def api_preview_telegram_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = preview_telegram_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.post("/variants/{variant_id}/telegram/send-test")
def api_send_telegram_test(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = send_telegram_test_from_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with Telegram routes.")


write_file(
    "backend/tests/smoke_test_telegram_connector.py",
    r'''
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
    ''',
)


write_file(
    "frontend/src/components/telegram-connection-test-action.tsx",
    r'''
"use client";

import { useState } from "react";

type TelegramConnectionTestActionProps = {
  apiBaseUrl: string;
};

export function TelegramConnectionTestAction({
  apiBaseUrl
}: TelegramConnectionTestActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  async function handleTest() {
    setIsTesting(true);
    setMessage("");
    setRaw(null);

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/telegram/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ mode })
      });

      const payload = await response.json();
      setRaw(payload);
      setMessage(payload.message ?? `HTTP ${response.status}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">تست اتصال</p>
        <h2>اتصال تلگرام را بررسی کن</h2>
      </div>

      <div className="enhance-variant-action">
        <label>
          حالت تست
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="telegram">تست واقعی Bot</option>
          </select>
        </label>

        <button type="button" onClick={handleTest} disabled={isTesting}>
          {isTesting ? "در حال تست..." : "تست تلگرام"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}
      </div>

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/telegram-preview-test-send-action.tsx",
    r'''
"use client";

import { useState } from "react";

type TelegramPreviewTestSendActionProps = {
  apiBaseUrl: string;
  variantId: string;
  variantStatus: string;
  channelType: string;
};

export function TelegramPreviewTestSendAction({
  apiBaseUrl,
  variantId,
  variantStatus,
  channelType
}: TelegramPreviewTestSendActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [chatId, setChatId] = useState("");
  const [notes, setNotes] = useState("");
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [message, setMessage] = useState("");
  const [previewText, setPreviewText] = useState("");
  const [attemptLink, setAttemptLink] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  const canUse =
    channelType === "telegram" &&
    ["approved", "ready_for_publish", "scheduled"].includes(variantStatus);

  function payload() {
    return {
      mode,
      chat_id: chatId,
      notes,
      requested_by: "اپراتور دامامدیا",
      disable_web_page_preview: true
    };
  }

  async function handlePreview() {
    setIsPreviewing(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/telegram/preview`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload())
        }
      );

      const data = await response.json();
      setRaw(data);
      setPreviewText(data.text ?? "");

      if (!response.ok) {
        setMessage(`خطا در پیش‌نمایش تلگرام: HTTP ${response.status}`);
        return;
      }

      setMessage(data.ok ? "پیش‌نمایش تلگرام آماده است." : "این نسخه برای تلگرام هنوز مشکل دارد.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsPreviewing(false);
    }
  }

  async function handleSendTest() {
    setIsSending(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/telegram/send-test`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload())
        }
      );

      const data = await response.json();
      setRaw(data);

      const attemptId = data.attempt?.id;

      if (attemptId) {
        setAttemptLink(`/publishing/attempts/${attemptId}`);
      }

      if (!response.ok) {
        setMessage(`خطا در ارسال تست تلگرام: HTTP ${response.status}`);
        return;
      }

      const status = data.attempt?.status ?? "unknown";

      if (status === "test_sent") {
        setMessage("پیام تست تلگرام ارسال شد.");
      } else if (status === "dry_run") {
        setMessage("Dry-run انجام شد. هیچ پیامی به تلگرام ارسال نشد.");
      } else {
        setMessage(data.message ?? status);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">تلگرام</p>
        <h2>پیش‌نمایش و ارسال تست تلگرام</h2>
      </div>

      {channelType !== "telegram" ? (
        <p className="muted-note">
          این نسخه برای تلگرام نیست؛ بنابراین ارسال تست تلگرام روی آن فعال نیست.
        </p>
      ) : null}

      {channelType === "telegram" && !canUse ? (
        <p className="muted-note">
          قبل از ارسال تست، وضعیت نسخه باید «تأیید شده» یا «آماده انتشار» باشد.
        </p>
      ) : null}

      <div className="enhance-variant-action">
        <label>
          حالت ارسال
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="telegram">ارسال تست واقعی</option>
          </select>
        </label>

        <label>
          Chat ID / Channel
          <input
            value={chatId}
            onChange={(event) => setChatId(event.target.value)}
            placeholder="@channel_username یا chat_id"
          />
        </label>

        <label>
          یادداشت
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="مثلاً تست ارسال به کانال داخلی"
          />
        </label>

        <button
          type="button"
          onClick={handlePreview}
          disabled={isPreviewing || channelType !== "telegram"}
        >
          {isPreviewing ? "در حال ساخت پیش‌نمایش..." : "پیش‌نمایش تلگرام"}
        </button>

        <button
          type="button"
          onClick={handleSendTest}
          disabled={isSending || !canUse}
        >
          {isSending ? "در حال ارسال..." : "ارسال تست تلگرام"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}

        {attemptLink ? (
          <a className="inline-link" href={attemptLink}>
            مشاهده گزارش این تلاش
          </a>
        ) : null}
      </div>

      {previewText ? (
        <section className="panel nested-panel">
          <div className="panel-heading">
            <p className="eyebrow">Preview</p>
            <h3>متن آماده تلگرام</h3>
          </div>
          <pre className="generated-output">{previewText}</pre>
        </section>
      ) : null}

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/telegram/page.tsx",
    r'''
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { TelegramConnectionTestAction } from "../../../components/telegram-connection-test-action";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type TelegramConfig = {
  ready: boolean;
  missing: string[];
  bot_token_configured: boolean;
  default_chat_id_configured: boolean;
  default_chat_id_preview: string;
  secrets_redacted: boolean;
  message: string;
};

async function loadConfig(): Promise<TelegramConfig> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/telegram/config`, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return (await response.json()) as TelegramConfig;
  } catch {
    return {
      ready: false,
      missing: ["backend unreachable"],
      bot_token_configured: false,
      default_chat_id_configured: false,
      default_chat_id_preview: "",
      secrets_redacted: true,
      message: "Telegram config could not be loaded."
    };
  }
}

export default async function TelegramPublishingPage() {
  const config = await loadConfig();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تلگرام"
        title="وضعیت اتصال تلگرام"
        lead="اینجا وضعیت Bot Token و امکان ارسال تست تلگرام را بررسی می‌کنی. انتشار عمومی هنوز فعال نیست."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="آماده اتصال واقعی" value={config.ready ? "بله" : "نه"} helper="وضعیت env تلگرام" />
        <StatCard label="Bot Token" value={config.bot_token_configured ? "تنظیم شده" : "نیست"} helper="secret مخفی است" />
        <StatCard label="Default Chat ID" value={config.default_chat_id_configured ? "تنظیم شده" : "نیست"} helper={config.default_chat_id_preview || "اختیاری"} />
        <StatCard label="Secrets" value={config.secrets_redacted ? "مخفی" : "نامشخص"} helper="توکن در UI نمایش داده نمی‌شود" />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Configuration</p>
            <h2>تنظیمات امن</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>پیام</strong>
              <span>{config.message}</span>
            </div>
            <div>
              <strong>Missing</strong>
              <span>{config.missing.length ? config.missing.join(", ") : ""}</span>
            </div>
            <div>
              <strong>Default Chat</strong>
              <span>{config.default_chat_id_preview || ""}</span>
            </div>
          </div>
        </section>

        <TelegramConnectionTestAction apiBaseUrl={API_BASE_URL} />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">راهنما</p>
          <h2>برای اتصال واقعی چه لازم است؟</h2>
        </div>

        <ol className="simple-steps">
          <li>در تلگرام با BotFather یک Bot بساز.</li>
          <li>Bot Token را داخل backend/.env.local بگذار.</li>
          <li>برای ارسال به کانال، Bot را admin کانال کن.</li>
          <li>شناسه کانال را به شکل @channel_username یا chat_id وارد کن.</li>
          <li>اول Dry-run بزن؛ بعد تست واقعی.</li>
        </ol>

        <pre className="json-block">
{`DAMA_TELEGRAM_BOT_TOKEN=123456:your-bot-token
DAMA_TELEGRAM_DEFAULT_CHAT_ID=@your_test_channel`}
        </pre>
      </section>
    </main>
  );
}
    ''',
)


# Patch variant detail page to include Telegram action.
variant_detail = ROOT / "frontend/src/app/publishing/variants/[variantId]/page.tsx"
page = variant_detail.read_text(encoding="utf-8")

if 'import { TelegramPreviewTestSendAction }' not in page:
    if 'import { CreateWordPressDraftAction }' in page:
        page = page.replace(
            'import { CreateWordPressDraftAction } from "../../../../components/create-wordpress-draft-action";',
            'import { CreateWordPressDraftAction } from "../../../../components/create-wordpress-draft-action";\nimport { TelegramPreviewTestSendAction } from "../../../../components/telegram-preview-test-send-action";',
            1,
        )
    else:
        page = page.replace(
            'import { ReviewPublishingVariantForm } from "../../../../components/review-publishing-variant-form";',
            'import { TelegramPreviewTestSendAction } from "../../../../components/telegram-preview-test-send-action";\nimport { ReviewPublishingVariantForm } from "../../../../components/review-publishing-variant-form";',
            1,
        )

if "<TelegramPreviewTestSendAction" not in page:
    insert = r'''
      <TelegramPreviewTestSendAction
        apiBaseUrl={API_BASE_URL}
        variantId={variant.id}
        variantStatus={variant.status}
        channelType={variant.channel_type}
      />
'''

    if "<CreateWordPressDraftAction" in page:
        page = page.replace(
            """      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشت‌ها</p>""",
            insert + """

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشت‌ها</p>""",
            1,
        )
    else:
        page = page.replace(
            """      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشت‌ها</p>""",
            insert + """

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشت‌ها</p>""",
            1,
        )

variant_detail.write_text(page, encoding="utf-8")
print("Patched variant detail page with Telegram action.")


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/projects", label: "پروژه‌ها" },
  { href: "/content-assets", label: "محتواها" },
  { href: "/generate", label: "تولید محتوا" },
  { href: "/publishing", label: "انتشار" },
  { href: "/publishing/variants", label: "نسخه‌سازی" },
  { href: "/publishing/wordpress", label: "وردپرس" },
  { href: "/publishing/telegram", label: "تلگرام" },
  { href: "/publishing/attempts", label: "گزارش انتشار" },
  { href: "/workflows", label: "جریان کار" },
  { href: "/search", label: "جستجو" },
  { href: "/runtime", label: "سلامت سیستم" },
  { href: "/operations", label: "عملیات" },
  { href: "/exports", label: "خروجی‌ها" },
  { href: "/maintenance", label: "نگهداری" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="ناوبری دامامدیا">
      {navItems.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "active" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Telegram connector */",
    r'''
/* Telegram connector */
.nested-panel {
  margin-top: 1rem;
  background: rgba(255, 255, 255, 0.55);
}
    ''',
)


append_once(
    "backend/.env.local.example",
    "DAMA_TELEGRAM_BOT_TOKEN",
    r'''
# Telegram Connector
DAMA_TELEGRAM_BOT_TOKEN=
DAMA_TELEGRAM_DEFAULT_CHAT_ID=
    ''',
)


append_once(
    ".env.example",
    "DAMA_TELEGRAM_BOT_TOKEN",
    r'''
# Telegram Connector
DAMA_TELEGRAM_BOT_TOKEN=
DAMA_TELEGRAM_DEFAULT_CHAT_ID=
    ''',
)


append_once(
    "docs/publishing-foundation.md",
    "## Telegram Preview / Test Send",
    r'''
## Telegram Preview / Test Send

Release Pack AF adds Telegram connector foundation.

Endpoints:

    GET /publishing/telegram/config
    POST /publishing/telegram/test
    POST /publishing/variants/{variant_id}/telegram/preview
    POST /publishing/variants/{variant_id}/telegram/send-test

Modes:

- dry_run
- telegram

Environment variables:

    DAMA_TELEGRAM_BOT_TOKEN
    DAMA_TELEGRAM_DEFAULT_CHAT_ID

Safety:

- Dry-run is the default.
- Bot token is never shown in the UI.
- Real send requires Bot Token and chat_id.
- Public scheduled publishing is not enabled yet.
    ''',
)


append_once(
    "docs/configuration.md",
    "## Telegram Connector",
    r'''
## Telegram Connector

For Telegram real test sending, set:

    DAMA_TELEGRAM_BOT_TOKEN=123456:your-bot-token
    DAMA_TELEGRAM_DEFAULT_CHAT_ID=@your_test_channel

For channel sending:

1. Create a bot with BotFather.
2. Add bot as admin to the target channel.
3. Use channel username as chat_id, for example:

       @your_channel

Never commit real bot tokens.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AF Completed",
    r'''
## Release Pack AF Completed

Name:

Telegram Preview / Test Send

Added files:

- backend/src/services/telegram_connector_service.py
- backend/tests/smoke_test_telegram_connector.py
- frontend/src/app/publishing/telegram/page.tsx
- frontend/src/components/telegram-connection-test-action.tsx
- frontend/src/components/telegram-preview-test-send-action.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/[variantId]/page.tsx
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- backend/.env.local.example
- .env.example
- docs/configuration.md
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- Telegram config status endpoint
- Telegram dry-run/real bot test endpoint
- Telegram preview for publishing variants
- Telegram dry-run send-test attempt
- Telegram real send-test path
- frontend Telegram status page
- variant detail action for Telegram preview/test send

Next recommended Release Pack:

Release Pack AG: Telegram Real Test Setup

Suggested scope:

- create Telegram bot
- configure backend/.env.local
- dry-run from UI
- real getMe test
- send one real test message to private test channel/group
- no scheduled public publishing yet
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack AF applied successfully.")
