from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import base64
import json
import os

from src.services.publishing_channel_service import get_channel
from src.services.publishing_variant_service import get_variant, read_variants, write_variants


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
ATTEMPTS_PATH = DATA_DIR / "publishing_attempts.json"


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


def list_publish_attempts(
    variant_id: str | None = None,
    channel_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    attempts = read_attempts()

    if variant_id:
        attempts = [item for item in attempts if item.get("variant_id") == variant_id]

    if channel_id:
        attempts = [item for item in attempts if item.get("channel_id") == channel_id]

    if status:
        attempts = [item for item in attempts if item.get("status") == status]

    return {
        "total": len(attempts),
        "items": attempts,
    }


def get_publish_attempt(attempt_id: str) -> dict[str, Any] | None:
    for attempt in read_attempts():
        if attempt.get("id") == attempt_id:
            return attempt

    return None


def safe_wordpress_config() -> dict[str, Any]:
    return {
        "base_url_configured": bool(os.getenv("DAMA_WORDPRESS_BASE_URL")),
        "username_configured": bool(os.getenv("DAMA_WORDPRESS_USERNAME")),
        "application_password_configured": bool(os.getenv("DAMA_WORDPRESS_APP_PASSWORD")),
        "secrets_redacted": True,
    }


def wordpress_env_config() -> tuple[str, str, str]:
    base_url = os.getenv("DAMA_WORDPRESS_BASE_URL", "").strip().rstrip("/")
    username = os.getenv("DAMA_WORDPRESS_USERNAME", "").strip()
    app_password = os.getenv("DAMA_WORDPRESS_APP_PASSWORD", "").strip()

    if not base_url or not username or not app_password:
        raise RuntimeError(
            "WordPress env is incomplete. Required: DAMA_WORDPRESS_BASE_URL, DAMA_WORDPRESS_USERNAME, DAMA_WORDPRESS_APP_PASSWORD."
        )

    return base_url, username, app_password


def wordpress_create_draft(
    title: str,
    content: str,
    excerpt: str = "",
) -> dict[str, Any]:
    base_url, username, app_password = wordpress_env_config()

    token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")

    payload = {
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "status": "draft",
    }

    request = Request(
        f"{base_url}/wp-json/wp/v2/posts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw)

    post_id = data.get("id")
    link = data.get("link")

    return {
        "wordpress_post_id": post_id,
        "wordpress_link": link,
        "wordpress_status": data.get("status", "draft"),
        "raw": {
            "id": post_id,
            "link": link,
            "status": data.get("status"),
            "type": data.get("type"),
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

        if attempt.get("status") == "draft_created":
            updated["status"] = "scheduled"

        variants[index] = updated
        write_variants(variants)
        return


def create_wordpress_draft_from_variant(
    variant_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    variant = get_variant(variant_id)

    if not variant:
        return None

    channel = get_channel(str(variant.get("channel_id") or ""))

    mode = str(payload.get("mode") or "dry_run").strip().lower()
    reviewed_by = str(payload.get("requested_by") or "operator").strip()
    extra_notes = str(payload.get("notes") or "").strip()

    attempt_id = str(uuid4())
    now = utc_now()

    attempt: dict[str, Any] = {
        "id": attempt_id,
        "variant_id": variant_id,
        "content_asset_id": variant.get("content_asset_id"),
        "channel_id": variant.get("channel_id"),
        "channel_name": variant.get("channel_name"),
        "channel_type": variant.get("channel_type"),
        "connector": "wordpress",
        "mode": mode,
        "requested_by": reviewed_by,
        "notes": extra_notes,
        "status": "created",
        "created_at": now,
        "updated_at": now,
        "target_url": channel.get("target_url") if channel else "",
        "variant_status_at_attempt": variant.get("status"),
        "safe_config": safe_wordpress_config(),
        "request_preview": {
            "title": variant.get("variant_title"),
            "content_preview": str(variant.get("variant_body") or "")[:1000],
            "status": "draft",
        },
        "response": {},
        "error": "",
    }

    if str(variant.get("channel_type") or "") != "wordpress":
        attempt["status"] = "blocked"
        attempt["error"] = "Variant channel_type is not wordpress."
    elif str(variant.get("status") or "") not in {"approved", "ready_for_publish", "scheduled"}:
        attempt["status"] = "blocked"
        attempt["error"] = "Variant must be approved or ready_for_publish before WordPress draft creation."
    elif mode == "dry_run":
        attempt["status"] = "dry_run"
        attempt["response"] = {
            "message": "Dry-run only. No WordPress request was sent.",
            "would_create": {
                "status": "draft",
                "title": variant.get("variant_title"),
            },
        }
    elif mode == "wordpress":
        try:
            result = wordpress_create_draft(
                title=str(variant.get("variant_title") or "DAMA Draft"),
                content=str(variant.get("variant_body") or ""),
                excerpt=str(payload.get("excerpt") or ""),
            )
            attempt["status"] = "draft_created"
            attempt["response"] = result
        except (RuntimeError, HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            attempt["status"] = "failed"
            attempt["error"] = str(exc)
    else:
        attempt["status"] = "blocked"
        attempt["error"] = f"Unsupported mode: {mode}"

    attempt["updated_at"] = utc_now()

    attempts = read_attempts()
    attempts.insert(0, attempt)
    write_attempts(attempts)

    update_variant_after_attempt(variant_id, attempt)

    return {
        "ok": attempt["status"] in {"dry_run", "draft_created"},
        "attempt": attempt,
        "message": attempt.get("error") or attempt["status"],
    }
