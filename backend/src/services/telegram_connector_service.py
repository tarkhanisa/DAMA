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

    with urlopen(request, timeout=float(os.getenv("DAMA_TELEGRAM_TIMEOUT_SECONDS", "8"))) as response:
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
