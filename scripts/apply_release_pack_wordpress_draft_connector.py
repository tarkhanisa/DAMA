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

    if "smoke_test_wordpress_draft_connector.py" in text:
        print("Skipped backend-check patch.")
        return

    if '"./backend/tests/smoke_test_publishing_review.py"' in text:
        text = text.replace(
            '"./backend/tests/smoke_test_publishing_review.py"',
            '"./backend/tests/smoke_test_publishing_review.py",\n    "./backend/tests/smoke_test_wordpress_draft_connector.py"',
            1,
        )
    elif '".\\backend\\tests\\smoke_test_publishing_review.py"' in text:
        text = text.replace(
            '".\\backend\\tests\\smoke_test_publishing_review.py"',
            '".\\backend\\tests\\smoke_test_publishing_review.py",\n    ".\\backend\\tests\\smoke_test_wordpress_draft_connector.py"',
            1,
        )
    else:
        text = text.rstrip() + r'''

$WordPressDraftSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_wordpress_draft_connector.py"
$WordPressDraftPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $WordPressDraftSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_wordpress_draft_connector.py..."
    & $WordPressDraftPython $WordPressDraftSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_wordpress_draft_connector.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\components\\create-wordpress-draft-action.tsx",',
        '".\\frontend\\src\\app\\publishing\\attempts\\page.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\components\\review-publishing-variant-form.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)
            else:
                marker = '".\\frontend\\src\\app\\publishing\\variants\\[variantId]\\page.tsx",'
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "WordPress draft action is missing connector endpoint." not in text:
        block = r'''
$WordPressDraftAction = Read-TextFile ".\frontend\src\components\create-wordpress-draft-action.tsx"
$PublishingAttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"

if ($WordPressDraftAction -notmatch "/wordpress/draft") {
    throw "WordPress draft action is missing connector endpoint."
}

if ($WordPressDraftAction -notmatch "dry_run") {
    throw "WordPress draft action must support dry_run mode."
}

if ($PublishingAttemptsPage -notmatch "/publishing/attempts") {
    throw "Publishing attempts page does not call attempts endpoint."
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
    ''',
)


write_file(
    "backend/src/api/publishing.py",
    r'''
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.services.publishing_channel_service import (
    create_channel,
    get_channel,
    list_channels,
    test_channel,
    update_channel,
)
from src.services.publishing_variant_ai_service import enhance_variant
from src.services.publishing_variant_service import (
    create_variants_plan,
    get_variant,
    list_variants,
    review_variant,
    update_variant_status,
)
from src.services.wordpress_draft_connector_service import (
    create_wordpress_draft_from_variant,
    get_publish_attempt,
    list_publish_attempts,
)


router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.get("/channels")
def api_list_channels() -> dict[str, Any]:
    return list_channels()


@router.post("/channels")
def api_create_channel(payload: dict[str, Any]) -> dict[str, Any]:
    return create_channel(payload)


@router.get("/channels/{channel_id}")
def api_get_channel(channel_id: str) -> dict[str, Any]:
    channel = get_channel(channel_id)

    if not channel:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return channel


@router.patch("/channels/{channel_id}")
def api_update_channel(channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    channel = update_channel(channel_id, payload)

    if not channel:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return channel


@router.post("/channels/{channel_id}/test")
def api_test_channel(channel_id: str) -> dict[str, Any]:
    result = test_channel(channel_id)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return result


@router.get("/variants")
def api_list_variants(
    content_asset_id: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_variants(
        content_asset_id=content_asset_id,
        channel_id=channel_id,
        status=status,
    )


@router.post("/variants/plan")
def api_create_variants_plan(payload: dict[str, Any]) -> dict[str, Any]:
    return create_variants_plan(payload)


@router.get("/variants/{variant_id}")
def api_get_variant(variant_id: str) -> dict[str, Any]:
    variant = get_variant(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


@router.patch("/variants/{variant_id}/status")
def api_update_variant_status(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    variant = update_variant_status(variant_id, str(payload.get("status") or "draft"))

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


@router.post("/variants/{variant_id}/enhance")
def api_enhance_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = enhance_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.patch("/variants/{variant_id}/review")
def api_review_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    variant = review_variant(variant_id, payload)

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


@router.post("/variants/{variant_id}/wordpress/draft")
def api_create_wordpress_draft(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = create_wordpress_draft_from_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.get("/attempts")
def api_list_publish_attempts(
    variant_id: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_publish_attempts(
        variant_id=variant_id,
        channel_id=channel_id,
        status=status,
    )


@router.get("/attempts/{attempt_id}")
def api_get_publish_attempt(attempt_id: str) -> dict[str, Any]:
    attempt = get_publish_attempt(attempt_id)

    if not attempt:
        raise HTTPException(status_code=404, detail="Publishing attempt not found.")

    return attempt
    ''',
)


write_file(
    "backend/tests/smoke_test_wordpress_draft_connector.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA WordPress Draft Smoke",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "WordPress draft connector smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-wordpress-draft-content-asset",
            "source_title": "تست پیش‌نویس وردپرس",
            "source_body": "این متن برای تست ساخت پیش‌نویس وردپرس در حالت dry-run ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان آماده پیش‌نویس وردپرس",
            "variant_body": "متن آماده برای ساخت پیش‌نویس وردپرس.",
            "review_notes": "آماده تست dry-run وردپرس.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    draft_response = client.post(
        f"/publishing/variants/{variant['id']}/wordpress/draft",
        json={
            "mode": "dry_run",
            "requested_by": "smoke-test",
            "notes": "Dry-run connector test.",
        },
    )
    assert draft_response.status_code == 200, draft_response.text

    payload = draft_response.json()
    assert payload["ok"] is True
    assert payload["attempt"]["status"] == "dry_run"
    assert payload["attempt"]["connector"] == "wordpress"

    attempts_response = client.get("/publishing/attempts")
    assert attempts_response.status_code == 200, attempts_response.text
    assert attempts_response.json()["total"] >= 1

    print("WordPress draft connector smoke test passed.")


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

export function CreateWordPressDraftAction({
  apiBaseUrl,
  variantId,
  variantStatus,
  channelType
}: CreateWordPressDraftActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [notes, setNotes] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");

  const canUse =
    channelType === "wordpress" &&
    ["approved", "ready_for_publish", "scheduled"].includes(variantStatus);

  async function handleCreateDraft() {
    setIsCreating(true);
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/wordpress/draft`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            mode,
            notes,
            requested_by: "اپراتور دامامدیا"
          })
        }
      );

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در ساخت پیش‌نویس وردپرس: HTTP ${response.status}`);
        return;
      }

      const status = payload.attempt?.status ?? "unknown";
      const link = payload.attempt?.response?.wordpress_link;

      if (status === "draft_created" && link) {
        setMessage(`پیش‌نویس وردپرس ساخته شد: ${link}`);
      } else if (status === "dry_run") {
        setMessage("Dry-run انجام شد. هیچ چیزی روی وردپرس ساخته نشد.");
      } else {
        setMessage(payload.message ?? status);
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
          یادداشت
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="مثلاً Draft برای بازبینی سردبیر"
          />
        </label>

        <button
          type="button"
          onClick={handleCreateDraft}
          disabled={isCreating || !canUse}
        >
          {isCreating ? "در حال انجام..." : "ساخت پیش‌نویس وردپرس"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}
      </div>

      <p className="muted-note">
        حالت Dry-run هیچ درخواستی به وردپرس نمی‌فرستد. برای اتصال واقعی باید متغیرهای محیطی وردپرس در .env تنظیم شده باشند.
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
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>هنوز تلاش انتشاری ثبت نشده است.</td>
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


# Patch variant detail page to include WordPress draft action.
variant_detail = ROOT / "frontend/src/app/publishing/variants/[variantId]/page.tsx"
page = variant_detail.read_text(encoding="utf-8")

if 'import { CreateWordPressDraftAction }' not in page:
    page = page.replace(
        'import { ReviewPublishingVariantForm } from "../../../../components/review-publishing-variant-form";',
        'import { CreateWordPressDraftAction } from "../../../../components/create-wordpress-draft-action";\nimport { ReviewPublishingVariantForm } from "../../../../components/review-publishing-variant-form";',
        1,
    )

if "<CreateWordPressDraftAction" not in page:
    page = page.replace(
        """      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشت‌ها</p>""",
        """      <CreateWordPressDraftAction
        apiBaseUrl={API_BASE_URL}
        variantId={variant.id}
        variantStatus={variant.status}
        channelType={variant.channel_type}
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشت‌ها</p>""",
        1,
    )

variant_detail.write_text(page, encoding="utf-8")
print("Patched variant detail page with WordPress draft action.")


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
    ".env.example",
    "DAMA_WORDPRESS_BASE_URL",
    r'''
# WordPress Draft Connector
# Used only when creating real WordPress drafts.
# Do not commit real credentials.
DAMA_WORDPRESS_BASE_URL=https://example.com
DAMA_WORDPRESS_USERNAME=your-wordpress-username
DAMA_WORDPRESS_APP_PASSWORD=your-wordpress-application-password
    ''',
)


append_once(
    "docs/publishing-foundation.md",
    "## WordPress Draft Connector",
    r'''
## WordPress Draft Connector

Release Pack AA adds the first real external publishing connector.

Endpoint:

    POST /publishing/variants/{variant_id}/wordpress/draft

Modes:

- dry_run
- wordpress

Dry-run mode does not send any request to WordPress.

WordPress mode creates a post with:

    status = draft

Required environment variables:

    DAMA_WORDPRESS_BASE_URL
    DAMA_WORDPRESS_USERNAME
    DAMA_WORDPRESS_APP_PASSWORD

Safety rules:

- No WordPress password is stored in the database.
- No token is entered through the frontend panel.
- Only approved / ready_for_publish WordPress variants can create drafts.
- Direct publish is not enabled.
    ''',
)


append_once(
    "docs/configuration.md",
    "## WordPress Draft Connector",
    r'''
## WordPress Draft Connector

For real WordPress draft creation, set local environment variables:

    DAMA_WORDPRESS_BASE_URL=https://your-site.com
    DAMA_WORDPRESS_USERNAME=your-wordpress-username
    DAMA_WORDPRESS_APP_PASSWORD=your-wordpress-application-password

The connector creates drafts only.

It does not publish directly.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AA Completed",
    r'''
## Release Pack AA Completed

Name:

WordPress Draft Connector

Added files:

- backend/src/services/wordpress_draft_connector_service.py
- backend/tests/smoke_test_wordpress_draft_connector.py
- frontend/src/components/create-wordpress-draft-action.tsx
- frontend/src/app/publishing/attempts/page.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/[variantId]/page.tsx
- frontend/src/components/app-nav.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- .env.example
- docs/publishing-foundation.md
- docs/configuration.md
- docs/project-status.md

Added behavior:

- WordPress draft connector
- dry-run mode
- real WordPress draft mode through environment variables
- publishing attempts log
- frontend action on variant detail page
- publishing attempts page

Next recommended Release Pack:

Release Pack AB: WordPress Config Helper + Draft Validation

Suggested scope:

- WordPress connection test endpoint
- safer config diagnostics
- better error messages
- post category/tag draft fields
- SEO field placeholders
- no direct publish yet
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack AA applied successfully.")
