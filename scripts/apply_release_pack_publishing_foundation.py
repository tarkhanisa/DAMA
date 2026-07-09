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


def patch_main() -> None:
    target = ROOT / "backend/src/main.py"
    text = target.read_text(encoding="utf-8")

    if "from src.api.publishing import router as publishing_router" not in text:
        lines = text.splitlines()
        insert_at = 0

        for index, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = index + 1

        lines.insert(insert_at, "from src.api.publishing import router as publishing_router")
        text = "\n".join(lines)

    if "app.include_router(publishing_router)" not in text:
        text = text.rstrip() + "\n\napp.include_router(publishing_router)\n"

    target.write_text(text.strip() + "\n", encoding="utf-8")
    print("Patched backend/src/main.py")


def patch_api_init() -> None:
    target = ROOT / "backend/src/api/__init__.py"
    text = target.read_text(encoding="utf-8") if target.exists() else ""

    if "publishing" not in text:
        text = text.rstrip() + "\nfrom . import publishing\n"

    target.write_text(text.strip() + "\n", encoding="utf-8")
    print("Patched backend/src/api/__init__.py")


def patch_backend_check() -> None:
    target = ROOT / "scripts/backend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "smoke_test_publishing.py" in text:
        print("Skipped backend-check patch.")
        return

    if '"./backend/tests/smoke_test_runtime.py"' in text:
        text = text.replace(
            '"./backend/tests/smoke_test_runtime.py"',
            '"./backend/tests/smoke_test_runtime.py",\n    "./backend/tests/smoke_test_publishing.py"',
            1,
        )
    elif '".\\backend\\tests\\smoke_test_runtime.py"' in text:
        text = text.replace(
            '".\\backend\\tests\\smoke_test_runtime.py"',
            '".\\backend\\tests\\smoke_test_runtime.py",\n    ".\\backend\\tests\\smoke_test_publishing.py"',
            1,
        )
    else:
        text = text.rstrip() + r'''

$PublishingSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_publishing.py"
$PublishingPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $PublishingSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_publishing.py..."
    & $PublishingPython $PublishingSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_publishing.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\publishing\\page.tsx",',
        '".\\frontend\\src\\components\\create-publishing-channel-form.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\generate\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Publishing page does not include channel creation form." not in text:
        block = r'''
$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$PublishingForm = Read-TextFile ".\frontend\src\components\create-publishing-channel-form.tsx"

if ($PublishingPage -notmatch "CreatePublishingChannelForm") {
    throw "Publishing page does not include channel creation form."
}

if ($PublishingForm -notmatch "/publishing/channels") {
    throw "Publishing form does not call publishing channels endpoint."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "backend/src/services/publishing_channel_service.py",
    r'''
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
    ''',
)


write_file(
    "backend/src/api/publishing.py",
    r'''
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.publishing_channel_service import (
    create_channel,
    get_channel,
    list_channels,
    test_channel,
    update_channel,
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
    ''',
)


write_file(
    "backend/tests/smoke_test_publishing.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    create_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Manual Review Channel",
            "channel_type": "manual",
            "target_url": "local-review",
            "notes": "Smoke test channel.",
        },
    )
    assert create_response.status_code == 200, create_response.text

    channel = create_response.json()
    assert channel["id"]
    assert channel["channel_type"] == "manual"

    list_response = client.get("/publishing/channels")
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()
    assert "items" in payload
    assert payload["total"] >= 1

    test_response = client.post(f"/publishing/channels/{channel['id']}/test")
    assert test_response.status_code == 200, test_response.text
    test_payload = test_response.json()
    assert test_payload["status"] in {"ready", "configured", "not_configured", "needs_review"}

    print("Publishing smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/create-publishing-channel-form.tsx",
    r'''
"use client";

import { FormEvent, useState } from "react";

type CreatePublishingChannelFormProps = {
  apiBaseUrl: string;
};

const channelTypes = [
  { value: "wordpress", label: "وردپرس" },
  { value: "telegram", label: "تلگرام" },
  { value: "instagram", label: "اینستاگرام" },
  { value: "linkedin", label: "لینکدین" },
  { value: "whatsapp", label: "واتساپ" },
  { value: "bale", label: "بله" },
  { value: "eitaa", label: "ایتا" },
  { value: "manual", label: "دستی / فقط بازبینی" }
];

export function CreatePublishingChannelForm({
  apiBaseUrl
}: CreatePublishingChannelFormProps) {
  const [name, setName] = useState("");
  const [channelType, setChannelType] = useState("wordpress");
  const [targetUrl, setTargetUrl] = useState("");
  const [publicHandle, setPublicHandle] = useState("");
  const [notes, setNotes] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/channels`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name,
          channel_type: channelType,
          target_url: targetUrl,
          public_handle: publicHandle,
          notes,
          status: "not_configured"
        })
      });

      if (!response.ok) {
        setMessage(`خطا در ساخت کانال: HTTP ${response.status}`);
        return;
      }

      setMessage("کانال ساخته شد. برای دیدن لیست، صفحه را refresh کن.");
      setName("");
      setTargetUrl("");
      setPublicHandle("");
      setNotes("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">کانال جدید</p>
        <h2>مسیر انتشار را تعریف کن</h2>
      </div>

      <label>
        نام کانال
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="مثلاً سایت گرگران، تلگرام اورماشاپ، اینستاگرام دامامدیا"
        />
      </label>

      <label>
        نوع کانال
        <select
          value={channelType}
          onChange={(event) => setChannelType(event.target.value)}
        >
          {channelTypes.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        آدرس یا مقصد عمومی
        <input
          value={targetUrl}
          onChange={(event) => setTargetUrl(event.target.value)}
          placeholder="مثلاً https://example.com یا @channel"
        />
      </label>

      <label>
        شناسه عمومی / handle
        <input
          value={publicHandle}
          onChange={(event) => setPublicHandle(event.target.value)}
          placeholder="مثلاً @damamedia یا نام صفحه"
        />
      </label>

      <label>
        توضیحات
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={4}
          placeholder="این کانال برای چه پروژه‌ای است؟ چه محدودیت‌هایی دارد؟"
        />
      </label>

      <p className="muted-note">
        در این مرحله token، password یا secret وارد نکن. این بخش فقط رجیستری امن کانال‌هاست.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving}>
        {isSaving ? "در حال ذخیره..." : "ساخت کانال"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/page.tsx",
    r'''
import { CreatePublishingChannelForm } from "../../components/create-publishing-channel-form";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingChannel = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
  target_url?: string;
  public_handle?: string;
  notes?: string;
  secret_configured?: boolean;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeChannels(payload: unknown): PublishingChannel[] {
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
        name: String(value.name ?? "کانال بدون نام"),
        channel_type: String(value.channel_type ?? "manual"),
        status: String(value.status ?? "not_configured"),
        target_url: typeof value.target_url === "string" ? value.target_url : "",
        public_handle:
          typeof value.public_handle === "string" ? value.public_handle : "",
        notes: typeof value.notes === "string" ? value.notes : "",
        secret_configured: Boolean(value.secret_configured)
      };
    })
    .filter((item) => item.id);
}

async function loadChannels(): Promise<PublishingChannel[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/channels`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeChannels(await response.json());
  } catch {
    return [];
  }
}

function channelTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    wordpress: "وردپرس",
    telegram: "تلگرام",
    instagram: "اینستاگرام",
    linkedin: "لینکدین",
    whatsapp: "واتساپ",
    bale: "بله",
    eitaa: "ایتا",
    manual: "دستی"
  };

  return labels[type] ?? type;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    not_configured: "تنظیم‌نشده",
    configured: "تنظیم‌شده",
    ready: "آماده",
    needs_review: "نیازمند بررسی",
    disabled: "غیرفعال",
    failed: "خطادار"
  };

  return labels[status] ?? status;
}

export default async function PublishingPage() {
  const channels = await loadChannels();
  const configuredCount = channels.filter((item) =>
    ["configured", "ready"].includes(item.status)
  ).length;
  const needsReviewCount = channels.filter((item) =>
    ["not_configured", "needs_review", "failed"].includes(item.status)
  ).length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار چندکاناله"
        title="کانال‌های انتشار"
        lead="اینجا مقصدهای انتشار را تعریف می‌کنی. در این مرحله هنوز انتشار واقعی انجام نمی‌شود؛ فقط نقشه کانال‌ها ساخته می‌شود."
      >
        <div className="actions">
          <a href="/generate">تولید محتوا</a>
          <a href="/content-assets">محتواها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه کانال‌ها" value={channels.length} helper="مقصدهای تعریف‌شده" />
        <StatCard label="آماده‌تر" value={configuredCount} helper="تنظیم‌شده یا آماده" />
        <StatCard label="نیازمند بررسی" value={needsReviewCount} helper="هنوز برای انتشار آماده نیستند" />
        <StatCard label="انتشار واقعی" value="بعداً" helper="در Releaseهای بعدی فعال می‌شود" />
      </section>

      <section className="two-column">
        <CreatePublishingChannelForm apiBaseUrl={API_BASE_URL} />

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">نقشه راه</p>
            <h2>بعد از این مرحله چه می‌شود؟</h2>
          </div>

          <ol className="simple-steps">
            <li>اول کانال‌ها را تعریف می‌کنیم.</li>
            <li>بعد برای هر محتوا نسخه مخصوص هر کانال ساخته می‌شود.</li>
            <li>بعد پیش‌نمایش و تأیید انسانی اضافه می‌شود.</li>
            <li>بعد اتصال واقعی وردپرس و تلگرام را فعال می‌کنیم.</li>
            <li>بعد صف انتشار و گزارش خطا ساخته می‌شود.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست کانال‌ها</p>
          <h2>مقصدهای انتشار</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>نام</th>
                <th>نوع</th>
                <th>وضعیت</th>
                <th>آدرس / handle</th>
                <th>Secret</th>
              </tr>
            </thead>
            <tbody>
              {channels.length > 0 ? (
                channels.map((channel) => (
                  <tr key={channel.id}>
                    <td>{channel.name}</td>
                    <td>{channelTypeLabel(channel.channel_type)}</td>
                    <td>
                      <span className={`status-badge status-${channel.status}`}>
                        {statusLabel(channel.status)}
                      </span>
                    </td>
                    <td>{channel.public_handle || channel.target_url || ""}</td>
                    <td>{channel.secret_configured ? "تنظیم شده" : "تنظیم نشده"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>هنوز کانالی تعریف نشده است.</td>
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
    "# Publishing Foundation",
    r'''
# Publishing Foundation

Release Pack W adds the first layer of DAMA multi-channel publishing.

## What It Adds

- publishing channel service
- publishing API
- publishing frontend page
- channel creation form
- safe channel registry
- no real publishing yet

## Backend

Endpoints:

    GET /publishing/channels
    POST /publishing/channels
    GET /publishing/channels/{channel_id}
    PATCH /publishing/channels/{channel_id}
    POST /publishing/channels/{channel_id}/test

## Supported Channel Types

- wordpress
- telegram
- instagram
- linkedin
- whatsapp
- bale
- eitaa
- manual

## Safety

This foundation does not store secrets.

Do not enter:

- passwords
- access tokens
- API keys
- bot tokens
- application passwords

Secrets will be handled later through a safer configuration layer.

## Next Step

Release Pack X should add channel-specific content variants.

Example:

One master content asset becomes:

- WordPress post version
- Telegram message version
- Instagram caption version
- LinkedIn post version
- Manual review version
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack W Completed",
    r'''
## Release Pack W Completed

Name:

Publishing Foundation + Channel Registry

Added files:

- backend/src/services/publishing_channel_service.py
- backend/src/api/publishing.py
- backend/tests/smoke_test_publishing.py
- frontend/src/app/publishing/page.tsx
- frontend/src/components/create-publishing-channel-form.tsx
- docs/publishing-foundation.md

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- frontend/src/components/app-nav.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- publishing channel registry
- channel creation API
- channel listing API
- channel test placeholder API
- Persian publishing page
- safe no-secret channel registration

Next recommended Release Pack:

Release Pack X: Channel Variant Generator

Suggested scope:

- choose content asset
- choose destination channels
- generate adapted variants
- WordPress version
- Telegram version
- Instagram caption version
- LinkedIn version
- manual review status
    ''',
)


patch_main()
patch_api_init()
patch_backend_check()
patch_frontend_check()

print("Release Pack W applied successfully.")
