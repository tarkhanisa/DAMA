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

    if "smoke_test_wordpress_flow_polish.py" in text:
        print("Skipped backend-check patch.")
        return

    text = text.rstrip() + r'''

$WordPressFlowPolishSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_wordpress_flow_polish.py"
$WordPressFlowPolishPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $WordPressFlowPolishSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_wordpress_flow_polish.py..."
    & $WordPressFlowPolishPython $WordPressFlowPolishSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_wordpress_flow_polish.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\publishing\\attempts\\[attemptId]\\page.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\publishing\\attempts\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Publishing attempt detail page is missing WordPress draft link support." not in text:
        block = r'''
$PublishingAttemptDetailPage = Read-TextFile ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx"
$WordPressDraftAction = Read-TextFile ".\frontend\src\components\create-wordpress-draft-action.tsx"
$PublishingAttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"

if ($PublishingAttemptDetailPage -notmatch "wordpress_link") {
    throw "Publishing attempt detail page is missing WordPress draft link support."
}

if ($WordPressDraftAction -notmatch "seo_title") {
    throw "WordPress draft action is missing SEO title field."
}

if ($WordPressDraftAction -notmatch "meta_description") {
    throw "WordPress draft action is missing meta description field."
}

if ($PublishingAttemptsPage -notmatch "/publishing/attempts/") {
    throw "Publishing attempts page does not link to attempt detail page."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "backend/src/services/wordpress_draft_connector_service.py",
    r'''
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
    ''',
)


write_file(
    "backend/tests/smoke_test_wordpress_flow_polish.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA WordPress Flow Polish",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "WordPress flow polish smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-wordpress-flow-polish",
            "source_title": "تست جزئیات تلاش انتشار",
            "source_body": "این متن برای تست صفحه جزئیات تلاش انتشار وردپرس ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان تست جزئیات Draft",
            "variant_body": "متن آماده برای تست جزئیات Draft وردپرس.",
            "review_notes": "آماده تست flow polish.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    draft_response = client.post(
        f"/publishing/variants/{variant['id']}/wordpress/draft",
        json={
            "mode": "dry_run",
            "excerpt": "خلاصه تست جزئیات",
            "slug": "wordpress-flow-polish-test",
            "categories": [1],
            "tags": [2],
            "seo_title": "عنوان سئوی تست",
            "meta_description": "توضیح متای کوتاه برای تست جریان وردپرس.",
            "requested_by": "smoke-test",
        },
    )
    assert draft_response.status_code == 200, draft_response.text
    payload = draft_response.json()
    assert payload["attempt"]["status"] == "dry_run"
    assert payload["attempt"]["request_preview"]["seo_title"]
    assert payload["attempt"]["request_preview"]["meta_description"]

    attempt_id = payload["attempt"]["id"]

    detail_response = client.get(f"/publishing/attempts/{attempt_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["id"] == attempt_id
    assert detail["request_preview"]["seo_title"] == "عنوان سئوی تست"

    print("WordPress flow polish smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/create-wordpress-draft-action.tsx",
    r'''
"use client";

import { useState } from "react";

type CreateWordPressDraftActionProps = {
  apiBaseUrl: string;
  variantId: string;
  variantStatus: string;
  channelType: string;
};

function parseNumberList(value: string): number[] {
  return value
    .split(",")
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((item) => Number.isFinite(item));
}

export function CreateWordPressDraftAction({
  apiBaseUrl,
  variantId,
  variantStatus,
  channelType
}: CreateWordPressDraftActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [excerpt, setExcerpt] = useState("");
  const [slug, setSlug] = useState("");
  const [categories, setCategories] = useState("");
  const [tags, setTags] = useState("");
  const [seoTitle, setSeoTitle] = useState("");
  const [metaDescription, setMetaDescription] = useState("");
  const [notes, setNotes] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [attemptLink, setAttemptLink] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  const canUse =
    channelType === "wordpress" &&
    ["approved", "ready_for_publish", "scheduled"].includes(variantStatus);

  function payload() {
    return {
      mode,
      excerpt,
      slug,
      categories: parseNumberList(categories),
      tags: parseNumberList(tags),
      seo_title: seoTitle,
      meta_description: metaDescription,
      notes,
      requested_by: "اپراتور دامامدیا"
    };
  }

  async function handleValidate() {
    setIsValidating(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/wordpress/validate`,
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

      if (!response.ok) {
        setMessage(`خطا در اعتبارسنجی: HTTP ${response.status}`);
        return;
      }

      if (data.ok) {
        setMessage(
          data.can_create_real_draft
            ? "این نسخه برای Draft واقعی آماده است."
            : "این نسخه برای Dry-run آماده است؛ env وردپرس هنوز برای Draft واقعی کامل نیست."
        );
      } else {
        setMessage("این نسخه هنوز مشکل دارد.");
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsValidating(false);
    }
  }

  async function handleCreateDraft() {
    setIsCreating(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/wordpress/draft`,
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
        setMessage(`خطا در ساخت پیش‌نویس وردپرس: HTTP ${response.status}`);
        return;
      }

      const status = data.attempt?.status ?? "unknown";
      const link = data.attempt?.response?.wordpress_link;

      if (status === "draft_created" && link) {
        setMessage(`پیش‌نویس وردپرس ساخته شد.`);
      } else if (status === "dry_run") {
        setMessage("Dry-run انجام شد. هیچ چیزی روی وردپرس ساخته نشد.");
      } else {
        setMessage(data.message ?? status);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">وردپرس</p>
        <h2>ساخت پیش‌نویس وردپرس</h2>
      </div>

      {channelType !== "wordpress" ? (
        <p className="muted-note">
          این نسخه برای وردپرس نیست؛ بنابراین ساخت Draft وردپرس روی آن فعال نیست.
        </p>
      ) : null}

      {channelType === "wordpress" && !canUse ? (
        <p className="muted-note">
          قبل از ساخت پیش‌نویس وردپرس، وضعیت نسخه باید «تأیید شده» یا «آماده انتشار» باشد.
        </p>
      ) : null}

      <div className="enhance-variant-action">
        <label>
          حالت اتصال
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="wordpress">ساخت Draft واقعی در وردپرس</option>
          </select>
        </label>

        <label>
          خلاصه / Excerpt
          <input
            value={excerpt}
            onChange={(event) => setExcerpt(event.target.value)}
            placeholder="خلاصه کوتاه برای وردپرس"
          />
        </label>

        <label>
          Slug
          <input
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
            placeholder="example-post-slug"
          />
        </label>

        <label>
          Categories ID
          <input
            value={categories}
            onChange={(event) => setCategories(event.target.value)}
            placeholder="مثلاً 3,7"
          />
        </label>

        <label>
          Tags ID
          <input
            value={tags}
            onChange={(event) => setTags(event.target.value)}
            placeholder="مثلاً 12,18"
          />
        </label>

        <label>
          SEO Title
          <input
            value={seoTitle}
            onChange={(event) => setSeoTitle(event.target.value)}
            placeholder="عنوان پیشنهادی سئو"
          />
        </label>

        <label>
          Meta Description
          <input
            value={metaDescription}
            onChange={(event) => setMetaDescription(event.target.value)}
            placeholder="توضیح متا برای سئو"
          />
        </label>

        <label>
          یادداشت
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="مثلاً Draft برای بازبینی سردبیر"
          />
        </label>

        <button
          type="button"
          onClick={handleValidate}
          disabled={isValidating || !canUse}
        >
          {isValidating ? "در حال بررسی..." : "اعتبارسنجی Draft"}
        </button>

        <button
          type="button"
          onClick={handleCreateDraft}
          disabled={isCreating || !canUse}
        >
          {isCreating ? "در حال انجام..." : "ساخت پیش‌نویس وردپرس"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}

        {attemptLink ? (
          <a className="inline-link" href={attemptLink}>
            مشاهده گزارش این تلاش
          </a>
        ) : null}
      </div>

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}

      <p className="muted-note">
        SEO title و meta description فعلاً در گزارش تلاش ذخیره می‌شوند. ارسال مستقیم به افزونه‌های سئو فقط وقتی فعال می‌شود که DAMA_WORDPRESS_SEND_SEO_META را عمداً فعال کنی.
      </p>
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/attempts/page.tsx",
    r'''
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingAttempt = {
  id: string;
  variant_id: string;
  channel_name: string;
  channel_type: string;
  connector: string;
  mode: string;
  status: string;
  created_at: string;
  error?: string;
  response?: Record<string, unknown>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeAttempts(payload: unknown): PublishingAttempt[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : Array.isArray(record.items)
      ? record.items
      : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        variant_id: String(value.variant_id ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? ""),
        connector: String(value.connector ?? ""),
        mode: String(value.mode ?? ""),
        status: String(value.status ?? ""),
        created_at: String(value.created_at ?? ""),
        error: typeof value.error === "string" ? value.error : "",
        response: asRecord(value.response)
      };
    })
    .filter((item) => item.id);
}

async function loadAttempts(): Promise<PublishingAttempt[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/attempts`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeAttempts(await response.json());
  } catch {
    return [];
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    dry_run: "Dry-run",
    draft_created: "Draft ساخته شد",
    failed: "خطا",
    blocked: "مسدود شده",
    created: "ساخته شده"
  };

  return labels[status] ?? status;
}

export default async function PublishingAttemptsPage() {
  const attempts = await loadAttempts();
  const draftCount = attempts.filter((item) => item.status === "draft_created").length;
  const dryRunCount = attempts.filter((item) => item.status === "dry_run").length;
  const failedCount = attempts.filter((item) => item.status === "failed").length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="گزارش انتشار"
        title="تلاش‌های انتشار"
        lead="اینجا تلاش‌های ساخت پیش‌نویس، dry-run و خطاهای اتصال ثبت می‌شوند."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing">کانال‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه تلاش‌ها" value={attempts.length} helper="همه connector attempts" />
        <StatCard label="Draft ساخته‌شده" value={draftCount} helper="اتصال واقعی موفق" />
        <StatCard label="Dry-run" value={dryRunCount} helper="تست امن بدون انتشار" />
        <StatCard label="خطا" value={failedCount} helper="نیازمند بررسی" />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست</p>
          <h2>آخرین تلاش‌ها</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>وضعیت</th>
                <th>کانال</th>
                <th>Connector</th>
                <th>Mode</th>
                <th>زمان</th>
                <th>پیام</th>
                <th>جزئیات</th>
              </tr>
            </thead>
            <tbody>
              {attempts.length > 0 ? (
                attempts.slice(0, 50).map((attempt) => (
                  <tr key={attempt.id}>
                    <td>
                      <span className={`status-badge status-${attempt.status}`}>
                        {statusLabel(attempt.status)}
                      </span>
                    </td>
                    <td>{attempt.channel_name || ""}</td>
                    <td>{attempt.connector}</td>
                    <td>{attempt.mode}</td>
                    <td>{attempt.created_at}</td>
                    <td>{attempt.error || String(attempt.response?.wordpress_link ?? "")}</td>
                    <td>
                      <a href={`/publishing/attempts/${attempt.id}`}>مشاهده</a>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>هنوز تلاش انتشاری ثبت نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/attempts/[attemptId]/page.tsx",
    r'''
import { ErrorPanel } from "../../../../components/error-panel";
import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type AttemptDetailPageProps = {
  params: Promise<{
    attemptId: string;
  }>;
};

type PublishingAttempt = {
  id: string;
  variant_id: string;
  content_asset_id?: string;
  channel_id?: string;
  channel_name?: string;
  channel_type?: string;
  connector?: string;
  mode?: string;
  requested_by?: string;
  notes?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  target_url?: string;
  request_preview?: Record<string, unknown>;
  response?: Record<string, unknown>;
  error?: string;
  error_detail?: Record<string, unknown>;
  validation?: Record<string, unknown>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadAttempt(attemptId: string): Promise<PublishingAttempt | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/attempts/${attemptId}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as PublishingAttempt;
  } catch {
    return null;
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    dry_run: "Dry-run",
    draft_created: "Draft ساخته شد",
    failed: "خطا",
    blocked: "مسدود شده",
    created: "ساخته شده"
  };

  return labels[status] ?? status;
}

export default async function PublishingAttemptDetailPage({
  params
}: AttemptDetailPageProps) {
  const { attemptId } = await params;
  const attempt = await loadAttempt(attemptId);

  if (!attempt) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="گزارش انتشار"
          title="تلاش انتشار پیدا نشد"
          message="این گزارش در بک‌اند پیدا نشد."
        />
      </main>
    );
  }

  const response = asRecord(attempt.response);
  const requestPreview = asRecord(attempt.request_preview);
  const validation = asRecord(attempt.validation);
  const errorDetail = asRecord(attempt.error_detail);

  const wordpressLink = String(response.wordpress_link ?? "");
  const wordpressPostId = String(response.wordpress_post_id ?? "");

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="جزئیات تلاش انتشار"
        title={`${attempt.connector ?? "connector"}  ${statusLabel(attempt.status)}`}
        lead="این صفحه گزارش دقیق یک تلاش انتشار یا ساخت Draft را نشان می‌دهد."
      >
        <div className="actions">
          <a href="/publishing/attempts">بازگشت به گزارش‌ها</a>
          <a href={`/publishing/variants/${attempt.variant_id}`}>بازگشت به نسخه</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(attempt.status)} helper={attempt.mode ?? ""} />
        <StatCard label="کانال" value={attempt.channel_name ?? ""} helper={attempt.channel_type ?? ""} />
        <StatCard label="درخواست‌کننده" value={attempt.requested_by ?? ""} helper={attempt.created_at ?? ""} />
        <StatCard label="WordPress Post" value={wordpressPostId || ""} helper="شناسه Draft در وردپرس" />
      </section>

      {wordpressLink ? (
        <section className="panel success-panel">
          <div className="panel-heading">
            <p className="eyebrow">Draft ساخته شد</p>
            <h2>لینک وردپرس</h2>
          </div>

          <p>
            پیش‌نویس وردپرس ساخته شده است. برای مشاهده یا ادامه ویرایش، لینک زیر را باز کن:
          </p>

          <a className="primary-link" href={wordpressLink} target="_blank" rel="noreferrer">
            باز کردن Draft وردپرس
          </a>
        </section>
      ) : null}

      {attempt.error ? (
        <section className="panel danger-panel">
          <div className="panel-heading">
            <p className="eyebrow">خطا</p>
            <h2>پیام خطا</h2>
          </div>

          <p>{attempt.error}</p>

          {Object.keys(errorDetail).length ? (
            <pre className="json-block">{JSON.stringify(errorDetail, null, 2)}</pre>
          ) : null}
        </section>
      ) : null}

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Request Preview</p>
            <h2>چیزی که قرار بود ساخته شود</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>Title</strong>
              <span>{String(requestPreview.title ?? "")}</span>
            </div>
            <div>
              <strong>Slug</strong>
              <span>{String(requestPreview.slug ?? "")}</span>
            </div>
            <div>
              <strong>Excerpt</strong>
              <span>{String(requestPreview.excerpt ?? "")}</span>
            </div>
            <div>
              <strong>SEO Title</strong>
              <span>{String(requestPreview.seo_title ?? "")}</span>
            </div>
            <div>
              <strong>Meta Description</strong>
              <span>{String(requestPreview.meta_description ?? "")}</span>
            </div>
          </div>

          <pre className="json-block">{JSON.stringify(requestPreview, null, 2)}</pre>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Validation</p>
            <h2>نتیجه اعتبارسنجی</h2>
          </div>

          <pre className="json-block">{JSON.stringify(validation, null, 2)}</pre>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Response</p>
          <h2>پاسخ Connector</h2>
        </div>

        <pre className="json-block">{JSON.stringify(response, null, 2)}</pre>
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Publishing attempt details */",
    r'''
/* Publishing attempt details */
.primary-link,
.inline-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  border-radius: 999px;
  padding: 0.65rem 1rem;
  background: var(--text);
  color: var(--surface);
  font-weight: 800;
  text-decoration: none;
}

.success-panel {
  border-color: rgba(63, 132, 88, 0.35);
}

.danger-panel {
  border-color: rgba(190, 75, 75, 0.35);
}
    ''',
)


append_once(
    ".env.example",
    "DAMA_WORDPRESS_SEND_SEO_META",
    r'''
# Optional. Default is disabled because many WordPress sites reject unregistered meta fields.
# Set to true only after verifying the SEO plugin supports REST meta updates.
DAMA_WORDPRESS_SEND_SEO_META=false
    ''',
)


append_once(
    "docs/publishing-foundation.md",
    "## WordPress Draft Flow Polish",
    r'''
## WordPress Draft Flow Polish

Release Pack AC improves WordPress draft attempt diagnostics.

Added behavior:

- publishing attempt detail page
- direct WordPress draft link when a real draft is created
- cleaner WordPress HTTP error formatting
- SEO title and meta description stored in request preview
- optional SEO meta sending through `DAMA_WORDPRESS_SEND_SEO_META`

Important:

SEO meta sending is disabled by default because WordPress may reject unregistered meta fields.

Direct publish is still not enabled.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AC Completed",
    r'''
## Release Pack AC Completed

Name:

Real WordPress Draft Flow Polish

Added files:

- backend/tests/smoke_test_wordpress_flow_polish.py
- frontend/src/app/publishing/attempts/[attemptId]/page.tsx

Updated files:

- backend/src/services/wordpress_draft_connector_service.py
- frontend/src/components/create-wordpress-draft-action.tsx
- frontend/src/app/publishing/attempts/page.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- .env.example
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- attempt detail page
- WordPress draft link support
- improved connector error details
- SEO title / meta description request preview
- optional SEO meta sending flag

Next recommended Release Pack:

Release Pack AD: Real WordPress Draft Test Setup

Suggested scope:

- step-by-step real WordPress env setup
- WordPress application password checklist
- real authentication test
- one real draft creation flow
- no direct publish yet
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack AC applied successfully.")
