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


write_file(
    "backend/src/services/runtime_cleanup_service.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import shutil


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
BACKUP_ROOT = BACKEND_ROOT / "backups" / "runtime-cleanup"

TARGET_FILES = {
    "channels": DATA_DIR / "publishing_channels.json",
    "variants": DATA_DIR / "publishing_variants.json",
    "attempts": DATA_DIR / "publishing_attempts.json",
    "queue": DATA_DIR / "publishing_queue.json",
}

PRESERVED_CHANNEL_NAMES = {
    "وردپرس لوکال دامامدیا",
    "تلگرام تست دامامدیا",
}

TEST_MARKERS = [
    "smoke",
    "smoke-test",
    "queue smoke",
    "damamedia_queue_test",
    "telegram-real-test",
    "dama queue telegram smoke",
    "dama telegram real test",
    "local test script",
    "first real telegram test",
    "publishing queue dry-run smoke",
    "تست صف انتشار",
    "تست ارسال واقعی",
    "تست تلگرام dama",
]

CHANNEL_TEST_MARKERS = [
    "smoke",
    "queue smoke",
    "damamedia_queue_test",
    "dama queue telegram smoke",
    "dama telegram real test",
    "telegram real test",
]


def utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def write_json_list(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def item_text(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True).lower()


def has_any_marker(item: dict[str, Any], markers: list[str]) -> bool:
    text = item_text(item)
    return any(marker.lower() in text for marker in markers)


def backup_data_dir() -> str:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup_dir = BACKUP_ROOT / utc_slug()
    backup_dir.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            target = backup_dir / item.name

            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    return str(backup_dir)


def split_channels(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    removed_ids: set[str] = set()

    for item in items:
        name = str(item.get("name") or "").strip()

        if name in PRESERVED_CHANNEL_NAMES:
            kept.append(item)
            continue

        if has_any_marker(item, CHANNEL_TEST_MARKERS):
            removed.append(item)
            item_id = str(item.get("id") or "").strip()
            if item_id:
                removed_ids.add(item_id)
            continue

        kept.append(item)

    return kept, removed, removed_ids


def split_variants(
    items: list[dict[str, Any]],
    removed_channel_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    removed_ids: set[str] = set()

    for item in items:
        item_id = str(item.get("id") or "").strip()
        channel_id = str(item.get("channel_id") or "").strip()

        should_remove = channel_id in removed_channel_ids or has_any_marker(item, TEST_MARKERS)

        if should_remove:
            removed.append(item)
            if item_id:
                removed_ids.add(item_id)
            continue

        kept.append(item)

    return kept, removed, removed_ids


def split_attempts(
    items: list[dict[str, Any]],
    removed_variant_ids: set[str],
    removed_channel_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for item in items:
        variant_id = str(item.get("variant_id") or "").strip()
        channel_id = str(item.get("channel_id") or "").strip()

        request = item.get("request")
        if isinstance(request, dict):
            variant_id = variant_id or str(request.get("variant_id") or "").strip()
            channel_id = channel_id or str(request.get("channel_id") or "").strip()

        should_remove = (
            variant_id in removed_variant_ids
            or channel_id in removed_channel_ids
            or has_any_marker(item, TEST_MARKERS)
        )

        if should_remove:
            removed.append(item)
            continue

        kept.append(item)

    return kept, removed


def split_queue(
    items: list[dict[str, Any]],
    removed_variant_ids: set[str],
    removed_channel_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for item in items:
        variant_id = str(item.get("variant_id") or "").strip()
        channel_id = str(item.get("channel_id") or "").strip()

        should_remove = (
            variant_id in removed_variant_ids
            or channel_id in removed_channel_ids
            or has_any_marker(item, TEST_MARKERS)
        )

        if should_remove:
            removed.append(item)
            continue

        kept.append(item)

    return kept, removed


def summarize_file(
    before_items: list[dict[str, Any]],
    after_items: list[dict[str, Any]],
    removed_items: list[dict[str, Any]],
) -> dict[str, Any]:
    removed_ids = [
        str(item.get("id") or "").strip()
        for item in removed_items
        if str(item.get("id") or "").strip()
    ]

    return {
        "before": len(before_items),
        "after": len(after_items),
        "removed": len(removed_items),
        "removed_ids": removed_ids[:50],
    }


def cleanup_test_runtime_data(
    dry_run: bool = True,
    backup: bool = True,
) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    channels = read_json_list(TARGET_FILES["channels"])
    variants = read_json_list(TARGET_FILES["variants"])
    attempts = read_json_list(TARGET_FILES["attempts"])
    queue = read_json_list(TARGET_FILES["queue"])

    kept_channels, removed_channels, removed_channel_ids = split_channels(channels)
    kept_variants, removed_variants, removed_variant_ids = split_variants(
        variants,
        removed_channel_ids,
    )
    kept_attempts, removed_attempts = split_attempts(
        attempts,
        removed_variant_ids,
        removed_channel_ids,
    )
    kept_queue, removed_queue = split_queue(
        queue,
        removed_variant_ids,
        removed_channel_ids,
    )

    summary = {
        "ok": True,
        "dry_run": dry_run,
        "backup_path": "",
        "files": {
            "publishing_channels.json": summarize_file(channels, kept_channels, removed_channels),
            "publishing_variants.json": summarize_file(variants, kept_variants, removed_variants),
            "publishing_attempts.json": summarize_file(attempts, kept_attempts, removed_attempts),
            "publishing_queue.json": summarize_file(queue, kept_queue, removed_queue),
        },
        "totals": {
            "removed": (
                len(removed_channels)
                + len(removed_variants)
                + len(removed_attempts)
                + len(removed_queue)
            )
        },
    }

    if dry_run:
        return summary

    if backup:
        summary["backup_path"] = backup_data_dir()

    write_json_list(TARGET_FILES["channels"], kept_channels)
    write_json_list(TARGET_FILES["variants"], kept_variants)
    write_json_list(TARGET_FILES["attempts"], kept_attempts)
    write_json_list(TARGET_FILES["queue"], kept_queue)

    return summary
    ''',
)


api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "from typing import Any" not in api:
    api = "from typing import Any\n" + api

if "runtime_cleanup_service" not in api:
    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\nfrom src.services.runtime_cleanup_service import cleanup_test_runtime_data\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/cleanup/test-data/preview")' not in api:
    api += r'''


@router.get("/cleanup/test-data/preview")
def api_preview_test_data_cleanup() -> dict[str, Any]:
    return cleanup_test_runtime_data(dry_run=True)


@router.post("/cleanup/test-data/run")
def api_run_test_data_cleanup(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = payload or {}
    backup = bool(request.get("backup", True))
    return cleanup_test_runtime_data(dry_run=False, backup=backup)
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with cleanup endpoints.")


write_file(
    "backend/tests/smoke_test_publishing_queue.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app
from src.services.runtime_cleanup_service import cleanup_test_runtime_data


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Queue Telegram Smoke",
            "channel_type": "telegram",
            "target_url": "@damamedia_queue_test",
            "notes": "Publishing queue smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-publishing-queue-content",
            "source_title": "تست صف انتشار",
            "source_body": "این متن برای تست صف انتشار DAMA ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "ready_for_publish",
            "variant_title": "عنوان تست صف انتشار",
            "variant_body": "متن آماده برای dry-run صف انتشار تلگرام.",
            "review_notes": "آماده صف انتشار.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    queue_response = client.post(
        "/publishing/queue",
        json={
            "variant_id": variant["id"],
            "connector": "telegram",
            "mode": "dry_run",
            "requested_by": "smoke-test",
            "notes": "Publishing queue dry-run smoke.",
            "run_payload": {
                "chat_id": "@damamedia_queue_test",
            },
        },
    )
    assert queue_response.status_code == 200, queue_response.text
    queue_item = queue_response.json()["item"]
    assert queue_item["status"] == "queued"

    run_response = client.post(
        f"/publishing/queue/{queue_item['id']}/run",
        json={
            "mode": "dry_run",
            "requested_by": "smoke-test",
        },
    )
    assert run_response.status_code == 200, run_response.text
    run_payload = run_response.json()

    assert run_payload["ok"] is True
    assert run_payload["item"]["status"] == "dry_run_completed"
    assert run_payload["item"]["latest_attempt_id"]

    list_response = client.get("/publishing/queue")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] >= 1

    cleanup_result = cleanup_test_runtime_data(dry_run=False, backup=False)
    assert cleanup_result["ok"] is True

    print("Publishing queue smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "scripts/cleanup_test_runtime_data.py",
    r'''
from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT = Path("I:/DAMA")
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from src.services.runtime_cleanup_service import cleanup_test_runtime_data  # noqa: E402


def main() -> None:
    preview = cleanup_test_runtime_data(dry_run=True)
    print("Preview:")
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    if preview["totals"]["removed"] == 0:
        print("No test runtime data found.")
        return

    result = cleanup_test_runtime_data(dry_run=False, backup=True)
    print("\nCleanup completed:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/cleanup-test-data-action.tsx",
    r'''
"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type CleanupTestDataActionProps = {
  apiBaseUrl: string;
};

export function CleanupTestDataAction({ apiBaseUrl }: CleanupTestDataActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function handleCleanup() {
    const confirmed = window.confirm(
      "داده‌های تستی صف، نسخه‌ها و گزارش‌ها پاک می‌شوند. قبل از حذف backup گرفته می‌شود. ادامه می‌دهی؟"
    );

    if (!confirmed) {
      return;
    }

    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/cleanup/test-data/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          backup: true
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(`HTTP ${response.status}`));
        return;
      }

      const removed = payload.totals?.removed ?? 0;
      const backupPath = payload.backup_path ? ` backup: ${payload.backup_path}` : "";

      setMessage(`پاک‌سازی انجام شد. تعداد حذف‌شده: ${removed}.${backupPath}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <button type="button" onClick={handleCleanup} disabled={isRunning}>
        {isRunning ? "در حال پاک‌سازی..." : "پاک‌سازی داده‌های تستی"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/app/advanced/cleanup/page.tsx",
    r'''
import { CleanupTestDataAction } from "../../../components/cleanup-test-data-action";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type FileSummary = {
  before?: number;
  after?: number;
  removed?: number;
};

type CleanupPreview = {
  ok?: boolean;
  totals?: {
    removed?: number;
  };
  files?: Record<string, FileSummary>;
};

async function loadPreview(): Promise<CleanupPreview> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/cleanup/test-data/preview`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return (await response.json()) as CleanupPreview;
  } catch {
    return {};
  }
}

export default async function AdvancedCleanupPage() {
  const preview = await loadPreview();
  const files = preview.files ?? {};
  const totalRemoved = preview.totals?.removed ?? 0;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="پیشرفته"
        title="پاک‌سازی داده‌های تستی"
        lead="این ابزار فقط آیتم‌های smoke/test را از داده‌های runtime پاک می‌کند و قبل از حذف backup می‌گیرد."
      >
        <div className="actions">
          <a href="/advanced">بازگشت به پیشرفته</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="قابل حذف" value={totalRemoved} helper="بر اساس preview فعلی" />
        <StatCard label="صف انتشار" value={files["publishing_queue.json"]?.removed ?? 0} helper="آیتم‌های تستی" />
        <StatCard label="نسخه‌ها" value={files["publishing_variants.json"]?.removed ?? 0} helper="variantهای تستی" />
        <StatCard label="گزارش‌ها" value={files["publishing_attempts.json"]?.removed ?? 0} helper="attemptهای تستی" />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">عملیات امن</p>
            <h2>پاک‌سازی با backup</h2>
          </div>

          <p className="muted-note">
            کانال‌های تمیز «وردپرس لوکال دامامدیا» و «تلگرام تست دامامدیا» حفظ می‌شوند.
            آیتم‌هایی که با smoke/test ساخته شده‌اند حذف می‌شوند.
          </p>

          <CleanupTestDataAction apiBaseUrl={API_BASE_URL} />
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>چه چیزی حذف می‌شود؟</h2>
          </div>

          <ol className="simple-steps">
            <li>کانال‌های smoke و تست موقت.</li>
            <li>نسخه‌هایی که برای smoke test ساخته شده‌اند.</li>
            <li>گزارش‌های اجرای آزمایشی تستی.</li>
            <li>آیتم‌های صف مربوط به تست‌ها.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش پیش‌نمایش فنی پاک‌سازی</summary>
          <pre className="json-block">{JSON.stringify(preview, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/advanced/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";

export const dynamic = "force-dynamic";

const advancedLinks = [
  {
    href: "/advanced/cleanup",
    title: "پاک‌سازی داده‌های تستی",
    description: "حذف امن smoke/test از صف، نسخه‌ها و گزارش‌ها با backup."
  },
  {
    href: "/runtime",
    title: "سلامت سیستم",
    description: "وضعیت backend، مدل‌ها و سرویس‌ها."
  },
  {
    href: "/operations",
    title: "عملیات",
    description: "ابزارهای عملیاتی و تست‌های داخلی."
  },
  {
    href: "/exports",
    title: "خروجی‌ها",
    description: "مدیریت خروجی‌های ساخته‌شده."
  },
  {
    href: "/maintenance",
    title: "نگهداری",
    description: "کارهای فنی و پاک‌سازی."
  },
  {
    href: "/workflows",
    title: "جریان کار",
    description: "مدیریت workflowهای داخلی."
  },
  {
    href: "/search",
    title: "جستجو",
    description: "جستجو در داده‌ها و محتواها."
  }
];

export default function AdvancedPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="پیشرفته"
        title="ابزارهای فنی و کم‌استفاده"
        lead="این بخش برای وقتی است که بخواهی وضعیت سیستم، پاک‌سازی داده‌ها یا ابزارهای فنی را بررسی کنی."
      >
        <div className="actions">
          <a href="/">داشبورد</a>
          <a href="/settings">تنظیمات</a>
        </div>
      </PageHeader>

      <section className="operator-grid">
        {advancedLinks.map((item) => (
          <a className="operator-card" href={item.href} key={item.href}>
            <span></span>
            <strong>{item.title}</strong>
            <p>{item.description}</p>
          </a>
        ))}
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path -LiteralPath ".\frontend\node_modules")) {
    throw "frontend/node_modules not found. Run npm install in frontend first."
}

Write-Host "node_modules found. Running frontend typecheck..."

Push-Location ".\frontend"
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Frontend typecheck failed."
}
Pop-Location

$RequiredFiles = @(
    ".\frontend\src\lib\persian-copy.ts",
    ".\frontend\src\components\cleanup-test-data-action.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx",
    ".\frontend\src\app\advanced\page.tsx",
    ".\frontend\src\app\advanced\cleanup\page.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$QueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$AttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"
$AttemptDetailPage = Read-TextFile ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx"
$AdvancedPage = Read-TextFile ".\frontend\src\app\advanced\page.tsx"
$CleanupPage = Read-TextFile ".\frontend\src\app\advanced\cleanup\page.tsx"
$CleanupAction = Read-TextFile ".\frontend\src\components\cleanup-test-data-action.tsx"

if ($HomePage -notmatch "dashboard-flow") {
    throw "Home page is missing visual dashboard flow."
}

if ($QueuePage -notmatch "labelQueueStatus") {
    throw "Queue page is not using Persian queue labels."
}

if ($AttemptsPage -notmatch "labelAttemptStatus") {
    throw "Attempts page is not using Persian attempt labels."
}

if ($AttemptDetailPage -notmatch "technical-details") {
    throw "Attempt detail page is missing collapsible technical details."
}

if ($AdvancedPage -notmatch "/advanced/cleanup") {
    throw "Advanced page does not link to cleanup page."
}

if ($CleanupPage -notmatch "/publishing/cleanup/test-data/preview") {
    throw "Cleanup page does not call cleanup preview endpoint."
}

if ($CleanupAction -notmatch "/publishing/cleanup/test-data/run") {
    throw "Cleanup action does not call cleanup run endpoint."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-3 Completed",
    r'''
## Release Pack AI-3 Completed

Name:

Smart Test Data Cleanup

Added files:

- backend/src/services/runtime_cleanup_service.py
- scripts/cleanup_test_runtime_data.py
- frontend/src/components/cleanup-test-data-action.tsx
- frontend/src/app/advanced/cleanup/page.tsx

Updated files:

- backend/src/api/publishing.py
- backend/tests/smoke_test_publishing_queue.py
- frontend/src/app/advanced/page.tsx
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- preview test runtime cleanup
- run test runtime cleanup with backup
- preserve clean real WordPress and Telegram channels
- remove smoke/test channels, variants, attempts and queue items
- publishing queue smoke test cleans its own runtime artifacts
- advanced cleanup page for safe manual cleanup

Next recommended step:

Release Pack AI-4: Guided Operator Checklist

Goal:

- show a step-by-step checklist in the UI
- guide the user from content generation to variants, queue and report review
- make the panel feel less like a technical dashboard and more like an operator console
    ''',
)


print("Release Pack AI-3 applied successfully.")
