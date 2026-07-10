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


def parse_int_list(value: Any) -> list[int]:
    if value is None:
        return []

    if isinstance(value, list):
        result: list[int] = []
        for item in value:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return result

    if isinstance(value, str):
        result = []
        for item in value.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                result.append(int(item))
            except ValueError:
                continue
        return result

    return []


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
                    message = str(parsed.get("message") or parsed.get("code") or message)
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


def wordpress_config_status() -> dict[str, Any]:
    base_url = os.getenv("DAMA_WORDPRESS_BASE_URL", "").strip().rstrip("/")
    username = os.getenv("DAMA_WORDPRESS_USERNAME", "").strip()
    app_password = os.getenv("DAMA_WORDPRESS_APP_PASSWORD", "").strip()

    missing = []

    if not base_url:
        missing.append("DAMA_WORDPRESS_BASE_URL")

    if not username:
        missing.append("DAMA_WORDPRESS_USERNAME")

    if not app_password:
        missing.append("DAMA_WORDPRESS_APP_PASSWORD")

    return {
        "ready": len(missing) == 0,
        "missing": missing,
        "base_url_configured": bool(base_url),
        "username_configured": bool(username),
        "application_password_configured": bool(app_password),
        "base_url_preview": base_url if base_url else "",
        "rest_posts_endpoint": f"{base_url}/wp-json/wp/v2/posts" if base_url else "",
        "rest_me_endpoint": f"{base_url}/wp-json/wp/v2/users/me" if base_url else "",
        "secrets_redacted": True,
        "message": "WordPress config is complete." if not missing else "WordPress config is incomplete.",
    }


def wordpress_env_config() -> tuple[str, str, str]:
    config = wordpress_config_status()

    if not config["ready"]:
        raise RuntimeError(
            "WordPress env is incomplete. Missing: " + ", ".join(config["missing"])
        )

    return (
        os.getenv("DAMA_WORDPRESS_BASE_URL", "").strip().rstrip("/"),
        os.getenv("DAMA_WORDPRESS_USERNAME", "").strip(),
        os.getenv("DAMA_WORDPRESS_APP_PASSWORD", "").strip(),
    )


def wordpress_auth_header(username: str, app_password: str) -> str:
    token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def wordpress_authenticated_get(path: str) -> dict[str, Any]:
    base_url, username, app_password = wordpress_env_config()

    request = Request(
        f"{base_url}{path}",
        headers={
            "Authorization": wordpress_auth_header(username, app_password),
            "Accept": "application/json",
        },
        method="GET",
    )

    with urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw) if raw else {}

    return data if isinstance(data, dict) else {"data": data}


def test_wordpress_connection(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode") or "dry_run").strip().lower()
    config = wordpress_config_status()

    if mode == "dry_run":
        return {
            "ok": True,
            "mode": mode,
            "ready_for_real_test": config["ready"],
            "config": config,
            "message": "Dry-run completed. No request was sent to WordPress.",
        }

    if mode != "wordpress":
        return {
            "ok": False,
            "mode": mode,
            "config": config,
            "message": f"Unsupported WordPress test mode: {mode}",
        }

    if not config["ready"]:
        return {
            "ok": False,
            "mode": mode,
            "config": config,
            "message": "WordPress config is incomplete.",
        }

    try:
        me = wordpress_authenticated_get("/wp-json/wp/v2/users/me")
        return {
            "ok": True,
            "mode": mode,
            "config": config,
            "wordpress_user": {
                "id": me.get("id"),
                "name": me.get("name"),
                "slug": me.get("slug"),
            },
            "message": "WordPress authentication test succeeded.",
        }
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError, RuntimeError) as exc:
        return {
            "ok": False,
            "mode": mode,
            "config": config,
            "error_detail": format_connector_exception(exc),
            "message": format_connector_exception(exc).get("message", str(exc)),
        }


def validate_wordpress_draft_variant(
    variant_id: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    variant = get_variant(variant_id)

    if not variant:
        return None

    payload = payload or {}
    channel = get_channel(str(variant.get("channel_id") or ""))
    config = wordpress_config_status()

    issues: list[str] = []
    warnings: list[str] = []

    if str(variant.get("channel_type") or "") != "wordpress":
        issues.append("این نسخه برای کانال وردپرس نیست.")

    if str(variant.get("status") or "") not in {"approved", "ready_for_publish", "scheduled"}:
        issues.append("وضعیت نسخه باید «تأیید شده» یا «آماده انتشار» باشد.")

    if not str(variant.get("variant_title") or "").strip():
        issues.append("عنوان نسخه خالی است.")

    if not str(variant.get("variant_body") or "").strip():
        issues.append("متن نسخه خالی است.")

    if channel and not str(channel.get("target_url") or "").strip():
        warnings.append("برای کانال وردپرس target_url عمومی ثبت نشده است.")

    if not config["ready"]:
        warnings.append("کانفیگ واقعی وردپرس در env کامل نیست؛ فقط dry-run امن قابل اتکاست.")

    categories = parse_int_list(payload.get("categories"))
    tags = parse_int_list(payload.get("tags"))
    excerpt = str(payload.get("excerpt") or "").strip()
    slug = str(payload.get("slug") or "").strip()
    seo_title = str(payload.get("seo_title") or "").strip()
    meta_description = str(payload.get("meta_description") or "").strip()

    if len(excerpt) > 300:
        warnings.append("excerpt طولانی است. بهتر است کوتاه‌تر شود.")

    if len(seo_title) > 80:
        warnings.append("SEO title طولانی است. بهتر است کوتاه‌تر شود.")

    if len(meta_description) > 170:
        warnings.append("meta description طولانی است. بهتر است کوتاه‌تر شود.")

    if slug and " " in slug:
        warnings.append("slug بهتر است بدون فاصله باشد.")

    return {
        "ok": len(issues) == 0,
        "can_dry_run": len(issues) == 0,
        "can_create_real_draft": len(issues) == 0 and config["ready"],
        "issues": issues,
        "warnings": warnings,
        "config": config,
        "variant": {
            "id": variant.get("id"),
            "title": variant.get("variant_title"),
            "status": variant.get("status"),
            "channel_type": variant.get("channel_type"),
            "channel_name": variant.get("channel_name"),
        },
        "field_preview": {
            "excerpt": excerpt,
            "slug": slug,
            "categories": categories,
            "tags": tags,
            "seo_title": seo_title,
            "meta_description": meta_description,
        },
    }


def build_optional_seo_meta(seo_title: str, meta_description: str) -> dict[str, str]:
    if os.getenv("DAMA_WORDPRESS_SEND_SEO_META", "").strip().lower() not in {"1", "true", "yes"}:
        return {}

    meta: dict[str, str] = {}

    if seo_title:
        meta["_yoast_wpseo_title"] = seo_title
        meta["rank_math_title"] = seo_title

    if meta_description:
        meta["_yoast_wpseo_metadesc"] = meta_description
        meta["rank_math_description"] = meta_description

    return meta


def wordpress_create_draft(
    title: str,
    content: str,
    excerpt: str = "",
    slug: str = "",
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    seo_title: str = "",
    meta_description: str = "",
) -> dict[str, Any]:
    base_url, username, app_password = wordpress_env_config()

    payload: dict[str, Any] = {
        "title": title,
        "content": content,
        "status": "draft",
    }

    if excerpt:
        payload["excerpt"] = excerpt

    if slug:
        payload["slug"] = slug

    if categories:
        payload["categories"] = categories

    if tags:
        payload["tags"] = tags

    optional_meta = build_optional_seo_meta(seo_title, meta_description)

    if optional_meta:
        payload["meta"] = optional_meta

    request = Request(
        f"{base_url}/wp-json/wp/v2/posts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": wordpress_auth_header(username, app_password),
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
    edit_link = ""

    links = data.get("_links")

    if isinstance(links, dict):
        edit_links = links.get("wp:action-edit")
        if isinstance(edit_links, list) and edit_links:
            first = edit_links[0]
            if isinstance(first, dict):
                edit_link = str(first.get("href") or "")

    return {
        "wordpress_post_id": post_id,
        "wordpress_link": link,
        "wordpress_edit_api_link": edit_link,
        "wordpress_status": data.get("status", "draft"),
        "seo_meta_sent": bool(optional_meta),
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
    excerpt = str(payload.get("excerpt") or "").strip()
    slug = str(payload.get("slug") or "").strip()
    categories = parse_int_list(payload.get("categories"))
    tags = parse_int_list(payload.get("tags"))
    seo_title = str(payload.get("seo_title") or "").strip()
    meta_description = str(payload.get("meta_description") or "").strip()

    validation = validate_wordpress_draft_variant(variant_id, payload)

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
        "safe_config": wordpress_config_status(),
        "validation": validation,
        "request_preview": {
            "title": variant.get("variant_title"),
            "content_preview": str(variant.get("variant_body") or "")[:1000],
            "status": "draft",
            "excerpt": excerpt,
            "slug": slug,
            "categories": categories,
            "tags": tags,
            "seo_title": seo_title,
            "meta_description": meta_description,
            "send_seo_meta_enabled": os.getenv("DAMA_WORDPRESS_SEND_SEO_META", "").strip().lower()
            in {"1", "true", "yes"},
        },
        "response": {},
        "error": "",
        "error_detail": {},
    }

    if not validation or not validation["ok"]:
        attempt["status"] = "blocked"
        attempt["error"] = "Draft validation failed."
    elif mode == "dry_run":
        attempt["status"] = "dry_run"
        attempt["response"] = {
            "message": "Dry-run only. No WordPress request was sent.",
            "would_create": attempt["request_preview"],
        }
    elif mode == "wordpress":
        if not validation["can_create_real_draft"]:
            attempt["status"] = "blocked"
            attempt["error"] = "WordPress config is incomplete or validation failed."
        else:
            try:
                result = wordpress_create_draft(
                    title=str(variant.get("variant_title") or "DAMA Draft"),
                    content=str(variant.get("variant_body") or ""),
                    excerpt=excerpt,
                    slug=slug,
                    categories=categories,
                    tags=tags,
                    seo_title=seo_title,
                    meta_description=meta_description,
                )
                attempt["status"] = "draft_created"
                attempt["response"] = result
            except (RuntimeError, HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                formatted = format_connector_exception(exc)
                attempt["status"] = "failed"
                attempt["error"] = str(formatted.get("message") or exc)
                attempt["error_detail"] = formatted
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
