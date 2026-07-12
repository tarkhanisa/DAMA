from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json

from src.services.publishing_variant_service import get_variant
from src.services.telegram_connector_service import send_telegram_test_from_variant
from src.services.wordpress_draft_connector_service import create_wordpress_draft_from_variant


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
QUEUE_PATH = DATA_DIR / "publishing_queue.json"


ALLOWED_QUEUE_STATUSES = {
    "queued",
    "running",
    "dry_run_completed",
    "sent",
    "failed",
    "blocked",
    "cancelled",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not QUEUE_PATH.exists():
        QUEUE_PATH.write_text("[]\n", encoding="utf-8")


def read_queue() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_queue(items: list[dict[str, Any]]) -> None:
    ensure_store()
    QUEUE_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_connector(value: str, variant: dict[str, Any] | None = None) -> str:
    connector = value.strip().lower()

    if connector:
        return connector

    if variant:
        channel_type = str(variant.get("channel_type") or "").strip().lower()

        if channel_type in {"wordpress", "telegram"}:
            return channel_type

    return "manual"


def normalize_mode(value: str) -> str:
    mode = value.strip().lower()

    if mode in {"dry_run", "wordpress", "telegram"}:
        return mode

    return "dry_run"


def list_queue(
    status: str | None = None,
    connector: str | None = None,
    variant_id: str | None = None,
) -> dict[str, Any]:
    items = read_queue()

    if status:
        items = [item for item in items if item.get("status") == status]

    if connector:
        items = [item for item in items if item.get("connector") == connector]

    if variant_id:
        items = [item for item in items if item.get("variant_id") == variant_id]

    return {
        "total": len(items),
        "items": items,
    }


def get_queue_item(queue_id: str) -> dict[str, Any] | None:
    for item in read_queue():
        if item.get("id") == queue_id:
            return item

    return None


def create_queue_item(payload: dict[str, Any]) -> dict[str, Any]:
    variant_id = str(payload.get("variant_id") or "").strip()
    variant = get_variant(variant_id)

    if not variant:
        return {
            "ok": False,
            "error": "Publishing variant not found.",
            "item": None,
        }

    connector = normalize_connector(str(payload.get("connector") or ""), variant)
    mode = normalize_mode(str(payload.get("mode") or "dry_run"))

    now = utc_now()

    item = {
        "id": str(uuid4()),
        "variant_id": variant_id,
        "content_asset_id": variant.get("content_asset_id"),
        "channel_id": variant.get("channel_id"),
        "channel_name": variant.get("channel_name"),
        "channel_type": variant.get("channel_type"),
        "variant_title": variant.get("variant_title"),
        "connector": connector,
        "mode": mode,
        "status": "queued",
        "priority": int(payload.get("priority") or 100),
        "requested_by": str(payload.get("requested_by") or "operator").strip(),
        "notes": str(payload.get("notes") or "").strip(),
        "run_payload": payload.get("run_payload") if isinstance(payload.get("run_payload"), dict) else {},
        "created_at": now,
        "updated_at": now,
        "started_at": "",
        "finished_at": "",
        "latest_attempt_id": "",
        "latest_attempt_status": "",
        "attempt_ids": [],
        "error": "",
        "history": [
            {
                "status": "queued",
                "at": now,
                "message": "Queue item created.",
            }
        ],
    }

    items = read_queue()
    items.insert(0, item)
    write_queue(items)

    return {
        "ok": True,
        "item": item,
    }


def update_queue_item(queue_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = read_queue()

    for index, item in enumerate(items):
        if item.get("id") != queue_id:
            continue

        updated = dict(item)
        updated.update(updates)
        updated["updated_at"] = utc_now()

        history = updated.get("history")
        if not isinstance(history, list):
            history = []

        if "status" in updates:
            history.append(
                {
                    "status": updates["status"],
                    "at": updated["updated_at"],
                    "message": str(updates.get("history_message") or ""),
                }
            )

        updated["history"] = history
        updated.pop("history_message", None)

        items[index] = updated
        write_queue(items)

        return updated

    return None


def map_attempt_status_to_queue_status(attempt_status: str) -> str:
    if attempt_status == "dry_run":
        return "dry_run_completed"

    if attempt_status in {"draft_created", "test_sent"}:
        return "sent"

    if attempt_status == "blocked":
        return "blocked"

    if attempt_status == "failed":
        return "failed"

    return "failed"


def run_queue_item(queue_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    item = get_queue_item(queue_id)

    if not item:
        return None

    if item.get("status") in {"running"}:
        return {
            "ok": False,
            "item": item,
            "message": "Queue item is already running.",
        }

    run_payload = dict(item.get("run_payload") or {})
    run_payload.update(payload or {})
    run_payload["mode"] = normalize_mode(str(run_payload.get("mode") or item.get("mode") or "dry_run"))
    run_payload["requested_by"] = str(run_payload.get("requested_by") or item.get("requested_by") or "operator")
    run_payload["notes"] = str(run_payload.get("notes") or item.get("notes") or "")

    update_queue_item(
        queue_id,
        {
            "status": "running",
            "started_at": utc_now(),
            "error": "",
            "history_message": "Queue item execution started.",
        },
    )

    connector = str(item.get("connector") or "").strip().lower()
    variant_id = str(item.get("variant_id") or "")

    try:
        if connector == "wordpress":
            result = create_wordpress_draft_from_variant(variant_id, run_payload)
        elif connector == "telegram":
            result = send_telegram_test_from_variant(variant_id, run_payload)
        else:
            result = {
                "ok": False,
                "attempt": {},
                "message": f"Unsupported queue connector: {connector}",
            }

        attempt = result.get("attempt") if isinstance(result, dict) else {}
        attempt = attempt if isinstance(attempt, dict) else {}
        attempt_id = str(attempt.get("id") or "")
        attempt_status = str(attempt.get("status") or "failed")
        queue_status = map_attempt_status_to_queue_status(attempt_status)

        attempt_ids = item.get("attempt_ids")
        if not isinstance(attempt_ids, list):
            attempt_ids = []

        if attempt_id:
            attempt_ids.insert(0, attempt_id)

        updated = update_queue_item(
            queue_id,
            {
                "status": queue_status,
                "finished_at": utc_now(),
                "latest_attempt_id": attempt_id,
                "latest_attempt_status": attempt_status,
                "attempt_ids": attempt_ids,
                "error": str(result.get("message") or attempt.get("error") or ""),
                "history_message": f"Connector finished with attempt status: {attempt_status}",
            },
        )

        return {
            "ok": queue_status in {"dry_run_completed", "sent"},
            "item": updated,
            "connector_result": result,
        }

    except Exception as exc:
        updated = update_queue_item(
            queue_id,
            {
                "status": "failed",
                "finished_at": utc_now(),
                "error": str(exc),
                "history_message": "Queue item execution failed.",
            },
        )

        return {
            "ok": False,
            "item": updated,
            "message": str(exc),
        }


def cancel_queue_item(queue_id: str) -> dict[str, Any] | None:
    item = get_queue_item(queue_id)

    if not item:
        return None

    if item.get("status") == "running":
        return {
            "ok": False,
            "item": item,
            "message": "Running queue items cannot be cancelled in this release.",
        }

    updated = update_queue_item(
        queue_id,
        {
            "status": "cancelled",
            "history_message": "Queue item cancelled.",
        },
    )

    return {
        "ok": True,
        "item": updated,
    }
