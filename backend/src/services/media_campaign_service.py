from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
CAMPAIGNS_PATH = DATA_DIR / "media_campaigns.json"


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


ALLOWED_CAMPAIGN_STATUSES = {
    "draft",
    "ready",
    "variant_planned",
    "queued",
    "published",
    "archived",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CAMPAIGNS_PATH.exists():
        CAMPAIGNS_PATH.write_text("[]\n", encoding="utf-8")


def read_campaigns() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(CAMPAIGNS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_campaigns(items: list[dict[str, Any]]) -> None:
    ensure_store()
    CAMPAIGNS_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def infer_media_type(value: str, explicit_type: str = "") -> str:
    media_type = explicit_type.strip().lower()

    if media_type in {"image", "video", "document", "other"}:
        return media_type

    suffix = Path(value.split("?")[0]).suffix.lower()

    if suffix in IMAGE_EXTENSIONS:
        return "image"

    if suffix in VIDEO_EXTENSIONS:
        return "video"

    return "other"


def normalize_media_item(item: Any) -> dict[str, Any] | None:
    if isinstance(item, str):
        value = item.strip()
        explicit_type = ""
        caption = ""
        alt = ""
    elif isinstance(item, dict):
        value = str(item.get("url") or item.get("path") or item.get("source") or "").strip()
        explicit_type = str(item.get("type") or "").strip()
        caption = str(item.get("caption") or "").strip()
        alt = str(item.get("alt") or "").strip()
    else:
        return None

    if not value:
        return None

    source_kind = "url" if value.startswith(("http://", "https://")) else "local_path"

    return {
        "id": str(uuid4()),
        "type": infer_media_type(value, explicit_type),
        "source": value,
        "source_kind": source_kind,
        "caption": caption,
        "alt": alt,
        "status": "attached",
    }


def normalize_media_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source = payload.get("media_items")

    if not isinstance(source, list):
        source = []

    media_items = [
        normalized
        for item in source
        if (normalized := normalize_media_item(item)) is not None
    ]

    media_urls = payload.get("media_urls")

    if isinstance(media_urls, str):
        media_urls = [line.strip() for line in media_urls.splitlines() if line.strip()]

    if isinstance(media_urls, list):
        for item in media_urls:
            normalized = normalize_media_item(item)
            if normalized:
                media_items.append(normalized)

    return media_items


def normalize_channel_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    channel_ids: list[str] = []

    for item in value:
        text = str(item).strip()

        if text and text not in channel_ids:
            channel_ids.append(text)

    return channel_ids


def campaign_preview_text(source_body: str) -> str:
    text = " ".join(source_body.split())

    if len(text) <= 180:
        return text

    return text[:177] + "..."


def list_media_campaigns(
    status: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    items = read_campaigns()

    if status:
        items = [item for item in items if item.get("status") == status]

    if project_id:
        items = [item for item in items if item.get("project_id") == project_id]

    return {
        "total": len(items),
        "items": items,
    }


def get_media_campaign(campaign_id: str) -> dict[str, Any] | None:
    for item in read_campaigns():
        if item.get("id") == campaign_id:
            return item

    return None


def create_media_campaign(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()

    source_title = str(payload.get("source_title") or payload.get("title") or "").strip()
    source_body = str(payload.get("source_body") or payload.get("body") or "").strip()

    if not source_title:
        source_title = "کمپین بدون عنوان"

    campaign = {
        "id": str(uuid4()),
        "project_id": str(payload.get("project_id") or "").strip(),
        "project_name": str(payload.get("project_name") or "").strip(),
        "source_title": source_title,
        "source_body": source_body,
        "preview": campaign_preview_text(source_body),
        "campaign_goal": str(payload.get("campaign_goal") or "").strip(),
        "language": str(payload.get("language") or "fa").strip() or "fa",
        "status": "draft",
        "channel_ids": normalize_channel_ids(payload.get("channel_ids")),
        "media_items": normalize_media_items(payload),
        "notes": str(payload.get("notes") or "").strip(),
        "created_at": now,
        "updated_at": now,
        "history": [
            {
                "status": "draft",
                "at": now,
                "message": "Media campaign created.",
            }
        ],
    }

    items = read_campaigns()
    items.insert(0, campaign)
    write_campaigns(items)

    return campaign


def update_media_campaign(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    items = read_campaigns()

    for index, item in enumerate(items):
        if item.get("id") != campaign_id:
            continue

        updated = dict(item)

        for field in [
            "project_id",
            "project_name",
            "source_title",
            "source_body",
            "campaign_goal",
            "language",
            "notes",
        ]:
            if field in payload:
                updated[field] = str(payload.get(field) or "").strip()

        if "status" in payload:
            next_status = str(payload.get("status") or "").strip()

            if next_status in ALLOWED_CAMPAIGN_STATUSES:
                updated["status"] = next_status

        if "channel_ids" in payload:
            updated["channel_ids"] = normalize_channel_ids(payload.get("channel_ids"))

        if "media_items" in payload or "media_urls" in payload:
            updated["media_items"] = normalize_media_items(payload)

        updated["preview"] = campaign_preview_text(str(updated.get("source_body") or ""))
        updated["updated_at"] = utc_now()

        history = updated.get("history")
        if not isinstance(history, list):
            history = []

        history.append(
            {
                "status": updated.get("status", "draft"),
                "at": updated["updated_at"],
                "message": "Media campaign updated.",
            }
        )

        updated["history"] = history

        items[index] = updated
        write_campaigns(items)

        return updated

    return None


def delete_media_campaign(campaign_id: str) -> bool:
    items = read_campaigns()
    next_items = [item for item in items if item.get("id") != campaign_id]

    if len(next_items) == len(items):
        return False

    write_campaigns(next_items)
    return True
