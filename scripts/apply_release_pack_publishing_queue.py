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

    if "smoke_test_publishing_queue.py" in text:
        print("Skipped backend-check patch.")
        return

    text = text.rstrip() + r'''

$PublishingQueueSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_publishing_queue.py"
$PublishingQueuePython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $PublishingQueueSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_publishing_queue.py..."
    & $PublishingQueuePython $PublishingQueueSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_publishing_queue.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\publishing\\queue\\page.tsx",',
        '".\\frontend\\src\\components\\create-publishing-queue-item-form.tsx",',
        '".\\frontend\\src\\components\\run-publishing-queue-item-action.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\publishing\\telegram\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Publishing queue page does not call queue endpoint." not in text:
        block = r'''
$PublishingQueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$PublishingQueueForm = Read-TextFile ".\frontend\src\components\create-publishing-queue-item-form.tsx"
$PublishingQueueRunAction = Read-TextFile ".\frontend\src\components\run-publishing-queue-item-action.tsx"

if ($PublishingQueuePage -notmatch "/publishing/queue") {
    throw "Publishing queue page does not call queue endpoint."
}

if ($PublishingQueueForm -notmatch "/publishing/queue") {
    throw "Publishing queue form does not call queue endpoint."
}

if ($PublishingQueueRunAction -notmatch "/run") {
    throw "Publishing queue run action is missing run endpoint."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "backend/src/services/publishing_queue_service.py",
    r'''
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
    ''',
)


api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "publishing_queue_service" not in api:
    queue_import = r'''
from src.services.publishing_queue_service import (
    cancel_queue_item,
    create_queue_item,
    get_queue_item,
    list_queue,
    run_queue_item,
)
'''.strip()

    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\n" + queue_import + "\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/queue")' not in api:
    api += r'''


@router.get("/queue")
def api_list_publishing_queue(
    status: str | None = Query(default=None),
    connector: str | None = Query(default=None),
    variant_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_queue(
        status=status,
        connector=connector,
        variant_id=variant_id,
    )


@router.post("/queue")
def api_create_publishing_queue_item(payload: dict[str, Any]) -> dict[str, Any]:
    result = create_queue_item(payload)

    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "Queue item could not be created.")

    return result


@router.get("/queue/{queue_id}")
def api_get_publishing_queue_item(queue_id: str) -> dict[str, Any]:
    item = get_queue_item(queue_id)

    if not item:
        raise HTTPException(status_code=404, detail="Publishing queue item not found.")

    return item


@router.post("/queue/{queue_id}/run")
def api_run_publishing_queue_item(queue_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = run_queue_item(queue_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing queue item not found.")

    return result


@router.post("/queue/{queue_id}/cancel")
def api_cancel_publishing_queue_item(queue_id: str) -> dict[str, Any]:
    result = cancel_queue_item(queue_id)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing queue item not found.")

    return result
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with queue routes.")


write_file(
    "backend/tests/smoke_test_publishing_queue.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


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

    print("Publishing queue smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/run-publishing-queue-item-action.tsx",
    r'''
"use client";

import { useState } from "react";

type RunPublishingQueueItemActionProps = {
  apiBaseUrl: string;
  queueId: string;
  status: string;
};

export function RunPublishingQueueItemAction({
  apiBaseUrl,
  queueId,
  status
}: RunPublishingQueueItemActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  const canRun = !["running", "sent", "cancelled"].includes(status);

  async function handleRun() {
    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/queue/${queueId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({})
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در اجرای صف: HTTP ${response.status}`);
        return;
      }

      const nextStatus = payload.item?.status ?? "unknown";
      setMessage(`اجرا انجام شد: ${nextStatus}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <button type="button" onClick={handleRun} disabled={isRunning || !canRun}>
        {isRunning ? "در حال اجرا..." : "اجرای صف"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/components/create-publishing-queue-item-form.tsx",
    r'''
"use client";

import { FormEvent, useState } from "react";

type PublishingVariantOption = {
  id: string;
  variant_title: string;
  channel_name: string;
  channel_type: string;
  status: string;
};

type CreatePublishingQueueItemFormProps = {
  apiBaseUrl: string;
  variants: PublishingVariantOption[];
};

export function CreatePublishingQueueItemForm({
  apiBaseUrl,
  variants
}: CreatePublishingQueueItemFormProps) {
  const [variantId, setVariantId] = useState(variants[0]?.id ?? "");
  const [connector, setConnector] = useState(variants[0]?.channel_type ?? "telegram");
  const [mode, setMode] = useState("dry_run");
  const [chatId, setChatId] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  function handleVariantChange(nextVariantId: string) {
    setVariantId(nextVariantId);
    const selected = variants.find((variant) => variant.id === nextVariantId);

    if (selected?.channel_type) {
      setConnector(selected.channel_type);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/queue`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          variant_id: variantId,
          connector,
          mode,
          requested_by: "اپراتور دامامدیا",
          notes,
          run_payload: {
            chat_id: chatId
          }
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(payload.detail ?? `خطا: HTTP ${response.status}`);
        return;
      }

      setMessage("آیتم به صف انتشار اضافه شد. صفحه را refresh کن.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">صف انتشار</p>
        <h2>افزودن نسخه به صف</h2>
      </div>

      <label>
        نسخه آماده انتشار
        <select value={variantId} onChange={(event) => handleVariantChange(event.target.value)}>
          {variants.length > 0 ? (
            variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.variant_title || "بدون عنوان"}  {variant.channel_name || variant.channel_type}  {variant.status}
              </option>
            ))
          ) : (
            <option value="">نسخه آماده‌ای وجود ندارد</option>
          )}
        </select>
      </label>

      <label>
        Connector
        <select value={connector} onChange={(event) => setConnector(event.target.value)}>
          <option value="wordpress">WordPress</option>
          <option value="telegram">Telegram</option>
        </select>
      </label>

      <label>
        Mode
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="dry_run">Dry-run امن</option>
          <option value="wordpress">WordPress Draft واقعی</option>
          <option value="telegram">Telegram تست واقعی</option>
        </select>
      </label>

      <label>
        Chat ID برای تلگرام
        <input
          value={chatId}
          onChange={(event) => setChatId(event.target.value)}
          placeholder="@channel_username یا خالی برای default"
        />
      </label>

      <label>
        یادداشت
        <input
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="مثلاً انتشار تست یا ارسال برای بازبینی"
        />
      </label>

      <p className="muted-note">
        حالت پیش‌فرض Dry-run است. برای اجرای واقعی، connector و mode باید عمداً انتخاب شود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving || !variantId}>
        {isSaving ? "در حال افزودن..." : "افزودن به صف"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/queue/page.tsx",
    r'''
import { CreatePublishingQueueItemForm } from "../../../components/create-publishing-queue-item-form";
import { PageHeader } from "../../../components/page-header";
import { RunPublishingQueueItemAction } from "../../../components/run-publishing-queue-item-action";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingQueueItem = {
  id: string;
  variant_id: string;
  variant_title: string;
  channel_name: string;
  channel_type: string;
  connector: string;
  mode: string;
  status: string;
  created_at: string;
  latest_attempt_id?: string;
  latest_attempt_status?: string;
  error?: string;
};

type PublishingVariantOption = {
  id: string;
  variant_title: string;
  channel_name: string;
  channel_type: string;
  status: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeQueue(payload: unknown): PublishingQueueItem[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        variant_id: String(value.variant_id ?? ""),
        variant_title: String(value.variant_title ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? ""),
        connector: String(value.connector ?? ""),
        mode: String(value.mode ?? ""),
        status: String(value.status ?? ""),
        created_at: String(value.created_at ?? ""),
        latest_attempt_id: String(value.latest_attempt_id ?? ""),
        latest_attempt_status: String(value.latest_attempt_status ?? ""),
        error: String(value.error ?? "")
      };
    })
    .filter((item) => item.id);
}

function normalizeVariants(payload: unknown): PublishingVariantOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        variant_title: String(value.variant_title ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? ""),
        status: String(value.status ?? "")
      };
    })
    .filter((item) => item.id)
    .filter((item) => ["approved", "ready_for_publish", "scheduled"].includes(item.status))
    .filter((item) => ["wordpress", "telegram"].includes(item.channel_type));
}

async function loadQueue(): Promise<PublishingQueueItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/queue`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeQueue(await response.json());
  } catch {
    return [];
  }
}

async function loadVariants(): Promise<PublishingVariantOption[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/variants`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeVariants(await response.json());
  } catch {
    return [];
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    queued: "در صف",
    running: "در حال اجرا",
    dry_run_completed: "Dry-run انجام شد",
    sent: "ارسال/ساخت انجام شد",
    failed: "خطا",
    blocked: "مسدود",
    cancelled: "لغو شده"
  };

  return labels[status] ?? status;
}

export default async function PublishingQueuePage() {
  const [queue, variants] = await Promise.all([loadQueue(), loadVariants()]);

  const queuedCount = queue.filter((item) => item.status === "queued").length;
  const sentCount = queue.filter((item) => item.status === "sent").length;
  const failedCount = queue.filter((item) => item.status === "failed" || item.status === "blocked").length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="صف انتشار"
        title="Publishing Queue"
        lead="اینجا نسخه‌های آماده انتشار را به صف اضافه می‌کنی و اجرای connectorها را دستی انجام می‌دهی."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه آیتم‌ها" value={queue.length} helper="همه صف" />
        <StatCard label="در صف" value={queuedCount} helper="منتظر اجرا" />
        <StatCard label="انجام‌شده" value={sentCount} helper="Draft یا Test Sent" />
        <StatCard label="خطادار" value={failedCount} helper="نیازمند بررسی" />
      </section>

      <section className="two-column">
        <CreatePublishingQueueItemForm apiBaseUrl={API_BASE_URL} variants={variants} />

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>روش امن استفاده</h2>
          </div>

          <ol className="simple-steps">
            <li>اول variant را در صفحه بازبینی روی آماده انتشار بگذار.</li>
            <li>بعد آن را به صف اضافه کن.</li>
            <li>اول Mode را Dry-run بگذار.</li>
            <li>اگر dry-run درست بود، بعداً mode واقعی را انتخاب کن.</li>
            <li>هر اجرا یک publishing attempt ثبت می‌کند.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست صف</p>
          <h2>آخرین آیتم‌ها</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>وضعیت</th>
                <th>عنوان</th>
                <th>کانال</th>
                <th>Connector</th>
                <th>Mode</th>
                <th>آخرین Attempt</th>
                <th>اجرا</th>
              </tr>
            </thead>
            <tbody>
              {queue.length > 0 ? (
                queue.slice(0, 50).map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span className={`status-badge status-${item.status}`}>
                        {statusLabel(item.status)}
                      </span>
                    </td>
                    <td>{item.variant_title || ""}</td>
                    <td>{item.channel_name || item.channel_type || ""}</td>
                    <td>{item.connector}</td>
                    <td>{item.mode}</td>
                    <td>
                      {item.latest_attempt_id ? (
                        <a href={`/publishing/attempts/${item.latest_attempt_id}`}>
                          {item.latest_attempt_status || "attempt"}
                        </a>
                      ) : (
                        ""
                      )}
                    </td>
                    <td>
                      <RunPublishingQueueItemAction
                        apiBaseUrl={API_BASE_URL}
                        queueId={item.id}
                        status={item.status}
                      />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>هنوز آیتمی در صف انتشار ثبت نشده است.</td>
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
  { href: "/publishing/queue", label: "صف انتشار" },
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
    "docs/publishing-foundation.md",
    "## Publishing Queue",
    r'''
## Publishing Queue

Release Pack AH adds a manual publishing queue.

Endpoints:

    GET /publishing/queue
    POST /publishing/queue
    GET /publishing/queue/{queue_id}
    POST /publishing/queue/{queue_id}/run
    POST /publishing/queue/{queue_id}/cancel

Supported connectors:

- wordpress
- telegram

Default mode:

- dry_run

Queue statuses:

- queued
- running
- dry_run_completed
- sent
- failed
- blocked
- cancelled

Safety:

- Queue execution is manual.
- Dry-run is the default.
- Real WordPress and Telegram modes must be intentionally selected.
- Every run creates a publishing attempt.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AH Completed",
    r'''
## Release Pack AH Completed

Name:

Publishing Queue

Added files:

- backend/src/services/publishing_queue_service.py
- backend/tests/smoke_test_publishing_queue.py
- frontend/src/app/publishing/queue/page.tsx
- frontend/src/components/create-publishing-queue-item-form.tsx
- frontend/src/components/run-publishing-queue-item-action.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/components/app-nav.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- manual publishing queue
- add approved/ready variants to queue
- run queue item manually
- WordPress and Telegram connector execution
- dry-run default
- queue status tracking
- attempt linking

Next recommended Release Pack:

Release Pack AI: Multi-channel Publish Dashboard

Suggested scope:

- one page for content asset  variants  queue
- select multiple channels
- generate variants
- add all to queue
- run dry-run batch
- no fully automatic public publishing yet
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack AH applied successfully.")
