from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
CHANNELS_PATH = DATA_DIR / "publishing_channels.json"


ALLOWED_CHANNEL_TYPES = {
    "wordpress",
    "telegram",
    "instagram",
    "linkedin",
    "whatsapp",
    "bale",
    "eitaa",
    "manual",
}

ALLOWED_STATUSES = {
    "not_configured",
    "configured",
    "ready",
    "needs_review",
    "disabled",
    "failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CHANNELS_PATH.exists():
        CHANNELS_PATH.write_text("[]\n", encoding="utf-8")


def read_channels() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(CHANNELS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_channels(channels: list[dict[str, Any]]) -> None:
    ensure_store()
    CHANNELS_PATH.write_text(
        json.dumps(channels, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_channel_type(channel_type: str) -> str:
    value = channel_type.strip().lower()

    if value not in ALLOWED_CHANNEL_TYPES:
        return "manual"

    return value


def normalize_status(status: str | None) -> str:
    if not status:
        return "not_configured"

    value = status.strip().lower()

    if value not in ALLOWED_STATUSES:
        return "not_configured"

    return value


def list_channels() -> dict[str, Any]:
    channels = read_channels()

    return {
        "total": len(channels),
        "items": channels,
    }


def get_channel(channel_id: str) -> dict[str, Any] | None:
    for channel in read_channels():
        if channel.get("id") == channel_id:
            return channel

    return None


def create_channel(payload: dict[str, Any]) -> dict[str, Any]:
    channels = read_channels()
    now = utc_now()

    name = str(payload.get("name") or "").strip()
    channel_type = normalize_channel_type(str(payload.get("channel_type") or "manual"))

    if not name:
        name = f"{channel_type.title()} Channel"

    channel = {
        "id": str(uuid4()),
        "name": name,
        "channel_type": channel_type,
        "status": normalize_status(payload.get("status")),
        "target_url": str(payload.get("target_url") or "").strip(),
        "public_handle": str(payload.get("public_handle") or "").strip(),
        "notes": str(payload.get("notes") or "").strip(),
        "settings_public": payload.get("settings_public")
        if isinstance(payload.get("settings_public"), dict)
        else {},
        "secret_configured": bool(payload.get("secret_configured", False)),
        "created_at": now,
        "updated_at": now,
    }

    channels.insert(0, channel)
    write_channels(channels)

    return channel


def update_channel(channel_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    channels = read_channels()

    for index, channel in enumerate(channels):
        if channel.get("id") != channel_id:
            continue

        updated = dict(channel)

        for key in ["name", "target_url", "public_handle", "notes"]:
            if key in payload:
                updated[key] = str(payload.get(key) or "").strip()

        if "channel_type" in payload:
            updated["channel_type"] = normalize_channel_type(str(payload.get("channel_type") or "manual"))

        if "status" in payload:
            updated["status"] = normalize_status(payload.get("status"))

        if isinstance(payload.get("settings_public"), dict):
            updated["settings_public"] = payload["settings_public"]

        if "secret_configured" in payload:
            updated["secret_configured"] = bool(payload.get("secret_configured"))

        updated["updated_at"] = utc_now()
        channels[index] = updated
        write_channels(channels)
        return updated

    return None


def test_channel(channel_id: str) -> dict[str, Any] | None:
    channel = get_channel(channel_id)

    if not channel:
        return None

    channel_type = channel.get("channel_type", "manual")
    target_url = channel.get("target_url", "")
    secret_configured = bool(channel.get("secret_configured", False))

    if channel_type == "manual":
        return {
            "channel_id": channel_id,
            "status": "ready",
            "can_publish": False,
            "message": "Manual channels are review-only and do not publish automatically.",
        }

    if not target_url:
        return {
            "channel_id": channel_id,
            "status": "needs_review",
            "can_publish": False,
            "message": "Target URL or channel address is missing.",
        }

    if channel_type in {"wordpress", "telegram", "instagram", "linkedin", "whatsapp", "bale", "eitaa"}:
        if not secret_configured:
            return {
                "channel_id": channel_id,
                "status": "not_configured",
                "can_publish": False,
                "message": "Secret/token is not configured yet. This foundation does not store secrets.",
            }

    return {
        "channel_id": channel_id,
        "status": "configured",
        "can_publish": False,
        "message": "Channel metadata is configured. Real connector is not implemented yet.",
    }
