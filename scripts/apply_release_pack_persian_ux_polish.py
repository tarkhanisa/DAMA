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


def rewrite_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"

    content = r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -Path $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path ".\frontend\node_modules")) {
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
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\settings\page.tsx",
    ".\frontend\src\app\advanced\page.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$QueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$QueueForm = Read-TextFile ".\frontend\src\components\create-publishing-queue-item-form.tsx"
$QueueRunAction = Read-TextFile ".\frontend\src\components\run-publishing-queue-item-action.tsx"
$PersianCopy = Read-TextFile ".\frontend\src\lib\persian-copy.ts"

$ExpectedNavRoutes = @(
    'href: "/"',
    'href: "/generate"',
    'href: "/publishing"',
    'href: "/projects"',
    'href: "/content-assets"',
    'href: "/settings"',
    'href: "/advanced"'
)

foreach ($Route in $ExpectedNavRoutes) {
    if ($AppNav -notmatch [regex]::Escape($Route)) {
        throw "Simplified navigation is missing route marker: $Route"
    }
}

$HiddenFromMainNav = @(
    'href: "/operations"',
    'href: "/runtime"',
    'href: "/exports"',
    'href: "/maintenance"',
    'href: "/workflows"',
    'href: "/search"'
)

foreach ($Route in $HiddenFromMainNav) {
    if ($AppNav -match [regex]::Escape($Route)) {
        throw "Technical route should not be in main nav: $Route"
    }
}

if ($PersianCopy -notmatch "labelQueueStatus") {
    throw "Persian copy helper is missing queue status labels."
}

if ($PersianCopy -notmatch "labelAttemptStatus") {
    throw "Persian copy helper is missing attempt status labels."
}

if ($HomePage -notmatch "dashboard-flow") {
    throw "Home page is missing visual dashboard flow."
}

if ($QueuePage -notmatch "labelQueueStatus") {
    throw "Queue page is not using Persian queue status labels."
}

if ($QueueForm -notmatch "labelConnector") {
    throw "Queue form is not using Persian connector labels."
}

if ($QueueRunAction -notmatch "labelQueueStatus") {
    throw "Queue run action is not using Persian status labels."
}

Write-Host "Frontend production readiness check passed."
'''

    target.write_text(content.strip() + "\n", encoding="utf-8-sig")
    print("Rewrote scripts/frontend-check.ps1")


write_file(
    "frontend/src/lib/persian-copy.ts",
    r'''
const queueStatusLabels: Record<string, string> = {
  queued: "در صف",
  running: "در حال اجرا",
  dry_run_completed: "اجرای آزمایشی انجام شد",
  sent: "انجام شد",
  failed: "خطا",
  blocked: "مسدود شده",
  cancelled: "لغو شده"
};

const attemptStatusLabels: Record<string, string> = {
  draft_created: "پیش‌نویس ساخته شد",
  test_sent: "پیام تست ارسال شد",
  dry_run: "اجرای آزمایشی انجام شد",
  failed: "خطا",
  blocked: "مسدود شده",
  pending: "در انتظار",
  ready: "آماده",
  unknown: "نامشخص"
};

const variantStatusLabels: Record<string, string> = {
  draft: "پیش‌نویس",
  ready_for_review: "آماده بازبینی",
  approved: "تأیید شده",
  ready_for_publish: "آماده انتشار",
  scheduled: "زمان‌بندی شده",
  published: "منتشر شده",
  rejected: "رد شده",
  failed: "خطا"
};

const connectorLabels: Record<string, string> = {
  wordpress: "وردپرس",
  telegram: "تلگرام",
  instagram: "اینستاگرام",
  linkedin: "لینکدین",
  whatsapp: "واتساپ",
  bale: "بله",
  eitaa: "ایتا",
  manual: "دستی"
};

const modeLabels: Record<string, string> = {
  dry_run: "اجرای آزمایشی امن",
  wordpress: "ساخت پیش‌نویس وردپرس",
  telegram: "ارسال تست تلگرام"
};

export function labelQueueStatus(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return queueStatusLabels[key] ?? "نامشخص";
}

export function labelAttemptStatus(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return attemptStatusLabels[key] ?? "نامشخص";
}

export function labelVariantStatus(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return variantStatusLabels[key] ?? "نامشخص";
}

export function labelConnector(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return connectorLabels[key] ?? "کانال";
}

export function labelMode(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return modeLabels[key] ?? "اجرای آزمایشی امن";
}

export function labelReady(value: boolean | undefined | null): string {
  return value ? "آماده" : "نیازمند بررسی";
}

export function friendlyErrorMessage(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  if (text.includes("Failed to fetch") || text.includes("fetch")) {
    return "ارتباط با سرور برقرار نشد.";
  }

  if (text.includes("HTTP 404")) {
    return "مسیر موردنظر پیدا نشد.";
  }

  if (text.includes("HTTP 500")) {
    return "خطای داخلی سرور رخ داد.";
  }

  if (text.toLowerCase().includes("timeout")) {
    return "زمان اتصال تمام شد. اتصال اینترنت یا VPN را بررسی کن.";
  }

  return text;
}
    ''',
)


write_file(
    "frontend/src/app/page.tsx",
    r'''
import { PageHeader } from "../components/page-header";
import { StatCard } from "../components/stat-card";
import { labelAttemptStatus, labelQueueStatus, labelReady } from "../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type RuntimeItem = Record<string, unknown>;

function asRecord(value: unknown): RuntimeItem {
  return value !== null && typeof value === "object" ? (value as RuntimeItem) : {};
}

function getItems(payload: unknown): RuntimeItem[] {
  const record = asRecord(payload);
  return Array.isArray(record.items) ? record.items.map(asRecord) : [];
}

async function loadJson(path: string): Promise<unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return await response.json();
  } catch {
    return {};
  }
}

export default async function HomePage() {
  const [wordpressConfig, telegramConfig, queuePayload, attemptsPayload] =
    await Promise.all([
      loadJson("/publishing/wordpress/config"),
      loadJson("/publishing/telegram/config"),
      loadJson("/publishing/queue"),
      loadJson("/publishing/attempts")
    ]);

  const wordpressReady = Boolean(asRecord(wordpressConfig).ready);
  const telegramReady = Boolean(asRecord(telegramConfig).ready);
  const queueItems = getItems(queuePayload);
  const attempts = getItems(attemptsPayload);

  const latestQueueStatus = labelQueueStatus(String(queueItems[0]?.status ?? ""));
  const latestAttemptStatus = labelAttemptStatus(String(attempts[0]?.status ?? ""));

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="DAMA"
        title="داشبورد ساده عملیات محتوا"
        lead="مسیر اصلی را از راست به چپ دنبال کن: محتوا بساز، نسخه آماده کن، وارد صف کن و نتیجه را بررسی کن."
      >
        <div className="actions">
          <a href="/generate">شروع تولید محتوا</a>
          <a href="/publishing/queue">رفتن به صف انتشار</a>
        </div>
      </PageHeader>

      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">نمای کلی</p>
          <h2>مسیر روزمره DAMA</h2>
          <p>
            این داشبورد برای استفاده روزانه ساده شده است. ابزارهای فنی در بخش
            پیشرفته قرار گرفته‌اند.
          </p>
        </div>

        <div className="connection-strip" aria-label="وضعیت اتصال‌ها">
          <span className={wordpressReady ? "connection-pill is-ready" : "connection-pill"}>
            وردپرس: {labelReady(wordpressReady)}
          </span>
          <span className={telegramReady ? "connection-pill is-ready" : "connection-pill"}>
            تلگرام: {labelReady(telegramReady)}
          </span>
        </div>
      </section>

      <section className="dashboard-flow" aria-label="شماتیک مسیر کار">
        <a className="flow-card primary-flow-card" href="/generate">
          <span className="flow-number">۱</span>
          <strong>تولید محتوا</strong>
          <p>متن مادر یا ایده اولیه را بساز.</p>
        </a>

        <span className="flow-arrow">←</span>

        <a className="flow-card" href="/publishing/variants">
          <span className="flow-number">۲</span>
          <strong>نسخه‌سازی</strong>
          <p>برای هر کانال متن مناسب بساز.</p>
        </a>

        <span className="flow-arrow">←</span>

        <a className="flow-card" href="/publishing/queue">
          <span className="flow-number">۳</span>
          <strong>صف انتشار</strong>
          <p>نسخه تأییدشده را دستی اجرا کن.</p>
        </a>

        <span className="flow-arrow">←</span>

        <a className="flow-card" href="/publishing/attempts">
          <span className="flow-number">۴</span>
          <strong>گزارش نتیجه</strong>
          <p>موفقیت یا خطا را بررسی کن.</p>
        </a>
      </section>

      <section className="stats-grid">
        <StatCard label="وردپرس" value={labelReady(wordpressReady)} helper="ساخت پیش‌نویس کنترل‌شده" />
        <StatCard label="تلگرام" value={labelReady(telegramReady)} helper="ارسال تست کنترل‌شده" />
        <StatCard label="آخرین صف" value={latestQueueStatus} helper={`${queueItems.length} آیتم ثبت‌شده`} />
        <StatCard label="آخرین گزارش" value={latestAttemptStatus} helper={`${attempts.length} گزارش ثبت‌شده`} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">کار پیشنهادی بعدی</p>
            <h2>از کجا شروع کنم؟</h2>
          </div>

          <ol className="simple-steps">
            <li>برای محتوای جدید، از «تولید محتوا» شروع کن.</li>
            <li>برای انتشار، اول نسخه کانالی بساز.</li>
            <li>قبل از اجرای واقعی، اجرای آزمایشی امن را بزن.</li>
            <li>بعد از اجرا، نتیجه را در گزارش‌ها ببین.</li>
          </ol>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">ابزارهای کمتر استفاده‌شده</p>
            <h2>همه چیز جلوی چشم نیست</h2>
          </div>

          <p>
            برای خلوتی پنل، سلامت سیستم، عملیات، نگهداری، خروجی‌ها و جستجو به بخش
            پیشرفته منتقل شده‌اند.
          </p>

          <div className="actions">
            <a href="/advanced">رفتن به پیشرفته</a>
            <a href="/settings">تنظیمات اتصال</a>
          </div>
        </section>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/components/create-publishing-queue-item-form.tsx",
    r'''
"use client";

import { FormEvent, useState } from "react";
import { friendlyErrorMessage, labelConnector, labelMode } from "../lib/persian-copy";

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
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("آیتم با موفقیت به صف انتشار اضافه شد. برای دیدن آن صفحه را تازه‌سازی کن.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">افزودن به صف</p>
        <h2>یک نسخه را برای انتشار آماده کن</h2>
      </div>

      <label>
        نسخه آماده انتشار
        <select value={variantId} onChange={(event) => handleVariantChange(event.target.value)}>
          {variants.length > 0 ? (
            variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.variant_title || "بدون عنوان"} — {variant.channel_name || labelConnector(variant.channel_type)}
              </option>
            ))
          ) : (
            <option value="">فعلاً نسخه آماده‌ای وجود ندارد</option>
          )}
        </select>
      </label>

      <label>
        مقصد انتشار
        <select value={connector} onChange={(event) => setConnector(event.target.value)}>
          <option value="wordpress">{labelConnector("wordpress")}</option>
          <option value="telegram">{labelConnector("telegram")}</option>
        </select>
      </label>

      <label>
        نوع اجرا
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="dry_run">{labelMode("dry_run")}</option>
          <option value="wordpress">{labelMode("wordpress")}</option>
          <option value="telegram">{labelMode("telegram")}</option>
        </select>
      </label>

      <label>
        شناسه گفت‌وگوی تلگرام
        <input
          value={chatId}
          onChange={(event) => setChatId(event.target.value)}
          placeholder="مثلاً @channel_username؛ اگر تنظیم پیش‌فرض داری، خالی بگذار"
        />
      </label>

      <label>
        یادداشت کوتاه
        <input
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="مثلاً: تست قبل از انتشار"
        />
      </label>

      <p className="muted-note">
        پیشنهاد امن: همیشه اول «اجرای آزمایشی امن» را انجام بده، بعد اجرای واقعی.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving || !variantId}>
        {isSaving ? "در حال افزودن..." : "افزودن به صف انتشار"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/components/run-publishing-queue-item-action.tsx",
    r'''
"use client";

import { useState } from "react";
import { friendlyErrorMessage, labelQueueStatus } from "../lib/persian-copy";

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
        setMessage(friendlyErrorMessage(`HTTP ${response.status}`));
        return;
      }

      const nextStatus = String(payload.item?.status ?? "unknown");
      setMessage(`نتیجه اجرا: ${labelQueueStatus(nextStatus)}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action compact-action">
      <button type="button" onClick={handleRun} disabled={isRunning || !canRun}>
        {isRunning ? "در حال اجرا..." : "اجرای آیتم"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
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
import {
  labelAttemptStatus,
  labelConnector,
  labelMode,
  labelQueueStatus
} from "../../../lib/persian-copy";

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

export default async function PublishingQueuePage() {
  const [queue, variants] = await Promise.all([loadQueue(), loadVariants()]);

  const queuedCount = queue.filter((item) => item.status === "queued").length;
  const doneCount = queue.filter((item) => item.status === "sent" || item.status === "dry_run_completed").length;
  const failedCount = queue.filter((item) => item.status === "failed" || item.status === "blocked").length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="صف انتشار"
        title="صف انتشار کنترل‌شده"
        lead="نسخه‌های آماده را اینجا وارد صف کن. اجرای واقعی همیشه دستی است و پیشنهاد می‌شود اول اجرای آزمایشی انجام شود."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه آیتم‌ها" value={queue.length} helper="کل صف فعلی" />
        <StatCard label="در صف" value={queuedCount} helper="منتظر اجرا" />
        <StatCard label="انجام‌شده" value={doneCount} helper="موفق یا آزمایشی" />
        <StatCard label="نیازمند بررسی" value={failedCount} helper="خطا یا مسدود شده" />
      </section>

      <section className="dashboard-flow compact-flow" aria-label="مسیر صف انتشار">
        <div className="flow-card">
          <span className="flow-number">۱</span>
          <strong>نسخه آماده</strong>
          <p>متن کانالی تأیید شده باشد.</p>
        </div>

        <span className="flow-arrow">←</span>

        <div className="flow-card">
          <span className="flow-number">۲</span>
          <strong>افزودن به صف</strong>
          <p>مقصد و نوع اجرا را انتخاب کن.</p>
        </div>

        <span className="flow-arrow">←</span>

        <div className="flow-card">
          <span className="flow-number">۳</span>
          <strong>اجرای دستی</strong>
          <p>اول آزمایشی، بعد واقعی.</p>
        </div>
      </section>

      <section className="two-column">
        <CreatePublishingQueueItemForm apiBaseUrl={API_BASE_URL} variants={variants} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنمای ساده</p>
            <h2>چطور اشتباه نکنم؟</h2>
          </div>

          <ol className="simple-steps">
            <li>برای تست، نوع اجرا را «اجرای آزمایشی امن» بگذار.</li>
            <li>برای وردپرس واقعی، فقط پیش‌نویس ساخته می‌شود.</li>
            <li>برای تلگرام واقعی، فعلاً فقط پیام تست ارسال می‌شود.</li>
            <li>هر اجرا در گزارش‌ها ثبت می‌شود.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">آیتم‌های صف</p>
          <h2>آخرین کارهای آماده اجرا</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>وضعیت</th>
                <th>نسخه</th>
                <th>کانال</th>
                <th>مقصد</th>
                <th>نوع اجرا</th>
                <th>آخرین نتیجه</th>
                <th>عملیات</th>
              </tr>
            </thead>
            <tbody>
              {queue.length > 0 ? (
                queue.slice(0, 50).map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span className={`status-badge status-${item.status}`}>
                        {labelQueueStatus(item.status)}
                      </span>
                    </td>
                    <td>{item.variant_title || "بدون عنوان"}</td>
                    <td>{item.channel_name || labelConnector(item.channel_type)}</td>
                    <td>{labelConnector(item.connector)}</td>
                    <td>{labelMode(item.mode)}</td>
                    <td>
                      {item.latest_attempt_id ? (
                        <a href={`/publishing/attempts/${item.latest_attempt_id}`}>
                          {labelAttemptStatus(item.latest_attempt_status)}
                        </a>
                      ) : (
                        "—"
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
                  <td colSpan={7}>فعلاً چیزی در صف انتشار نیست.</td>
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
    "frontend/src/app/settings/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { labelReady } from "../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ConnectorConfig = {
  ready?: boolean;
  message?: string;
};

async function loadConfig(path: string): Promise<ConnectorConfig> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return { ready: false, message: `HTTP ${response.status}` };
    }

    return (await response.json()) as ConnectorConfig;
  } catch {
    return { ready: false, message: "سرور محلی در دسترس نیست." };
  }
}

export default async function SettingsPage() {
  const [wordpress, telegram] = await Promise.all([
    loadConfig("/publishing/wordpress/config"),
    loadConfig("/publishing/telegram/config")
  ]);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تنظیمات"
        title="تنظیمات اتصال‌ها"
        lead="اینجا فقط وضعیت کلی اتصال‌های مهم را می‌بینی. اطلاعات محرمانه نمایش داده نمی‌شود."
      >
        <div className="actions">
          <a href="/publishing/wordpress">بررسی وردپرس</a>
          <a href="/publishing/telegram">بررسی تلگرام</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وردپرس" value={labelReady(Boolean(wordpress.ready))} helper={wordpress.message ?? "ساخت پیش‌نویس"} />
        <StatCard label="تلگرام" value={labelReady(Boolean(telegram.ready))} helper={telegram.message ?? "ارسال پیام تست"} />
        <StatCard label="حالت امن" value="فعال" helper="اجرای آزمایشی پیش‌فرض است" />
        <StatCard label="اطلاعات محرمانه" value="مخفی" helper="توکن‌ها در پنل نمایش داده نمی‌شوند" />
      </section>

      <section className="operator-grid">
        <a className="operator-card" href="/publishing/wordpress">
          <span>۱</span>
          <strong>وردپرس</strong>
          <p>وضعیت اتصال و ساخت پیش‌نویس را بررسی کن.</p>
        </a>

        <a className="operator-card" href="/publishing/telegram">
          <span>۲</span>
          <strong>تلگرام</strong>
          <p>وضعیت ربات و ارسال پیام تست را بررسی کن.</p>
        </a>

        <a className="operator-card" href="/advanced">
          <span>۳</span>
          <strong>پیشرفته</strong>
          <p>صفحات فنی، سلامت سیستم و ابزارهای نگهداری.</p>
        </a>
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Persian UX polish dashboard schematic */",
    r'''
/* Persian UX polish dashboard schematic */
.dashboard-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
  gap: 1rem;
  align-items: center;
  margin: 1.25rem 0;
  padding: 1.4rem;
  border: 1px solid var(--border);
  border-radius: 1.6rem;
  background:
    radial-gradient(circle at top right, rgba(35, 74, 112, 0.12), transparent 34%),
    rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow);
}

.dashboard-hero h2 {
  margin: 0.2rem 0 0.55rem;
}

.dashboard-hero p {
  margin: 0;
  color: var(--muted);
  line-height: 1.9;
}

.connection-strip {
  display: grid;
  gap: 0.65rem;
}

.connection-pill {
  display: inline-flex;
  justify-content: center;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--muted);
  font-weight: 800;
}

.connection-pill.is-ready {
  color: var(--text);
  background: rgba(255, 255, 255, 0.95);
}

.dashboard-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
  gap: 0.8rem;
  align-items: stretch;
  margin: 1.25rem 0;
}

.dashboard-flow.compact-flow {
  grid-template-columns: 1fr auto 1fr auto 1fr;
}

.flow-card {
  display: grid;
  gap: 0.55rem;
  min-height: 10rem;
  padding: 1.1rem;
  border: 1px solid var(--border);
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  text-decoration: none;
  box-shadow: var(--shadow);
}

.flow-card strong {
  font-size: 1.04rem;
}

.flow-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.primary-flow-card {
  background: rgba(255, 255, 255, 0.92);
  border-color: rgba(35, 74, 112, 0.35);
}

.flow-number {
  display: inline-flex;
  width: 2.2rem;
  height: 2.2rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(16, 25, 39, 0.08);
  font-weight: 900;
}

.flow-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-size: 1.4rem;
  font-weight: 900;
}

.quiet-panel {
  background: rgba(255, 255, 255, 0.56);
}

.compact-action button {
  padding-inline: 0.85rem;
  min-height: 2.5rem;
}

@media (max-width: 960px) {
  .dashboard-hero {
    grid-template-columns: 1fr;
  }

  .dashboard-flow,
  .dashboard-flow.compact-flow {
    grid-template-columns: 1fr;
  }

  .flow-arrow {
    transform: rotate(-90deg);
    min-height: 1rem;
  }
}
    ''',
)


write_file(
    "scripts/audit_frontend_persian_copy.py",
    r'''
from __future__ import annotations

from pathlib import Path
import re


ROOT = Path("I:/DAMA")
FRONTEND_SRC = ROOT / "frontend/src"
REPORT_PATH = ROOT / "docs/frontend-copy-audit.md"

SUSPICIOUS_TERMS = [
    "Dry-run",
    "dry-run",
    "Queue",
    "Attempt",
    "Connector",
    "Mode",
    "Run",
    "Test Send",
    "Ready",
    "Draft",
    "Publish",
    "WordPress",
    "Telegram",
    "unknown error",
    "Failed to fetch",
]

SKIP_FILES = {
    "frontend/src/lib/persian-copy.ts",
}

SKIP_PARTS = {
    ".next",
    "node_modules",
}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()

    if rel in SKIP_FILES:
        return True

    return any(part in path.parts for part in SKIP_PARTS)


def main() -> None:
    findings: list[str] = []

    for path in sorted(FRONTEND_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue

        if should_skip(path):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        for index, line in enumerate(lines, start=1):
            for term in SUSPICIOUS_TERMS:
                if term in line:
                    clean = re.sub(r"\s+", " ", line).strip()
                    rel = path.relative_to(ROOT).as_posix()
                    findings.append(f"- `{rel}:{index}` — `{term}` — `{clean}`")
                    break

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if findings:
        body = "\n".join(findings[:300])
        if len(findings) > 300:
            body += f"\n\n... and {len(findings) - 300} more findings.\n"
    else:
        body = "No obvious English UI copy terms were found."

    REPORT_PATH.write_text(
        "# Frontend Persian Copy Audit\n\n"
        "This report lists suspicious English UI terms that may still need Persian wording.\n\n"
        f"Total findings: {len(findings)}\n\n"
        f"{body}\n",
        encoding="utf-8",
    )

    print(f"Frontend copy audit completed. Findings: {len(findings)}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-1 Completed",
    r'''
## Release Pack AI-1 Completed

Name:

Persian UX Polish + Visual Dashboard Schematic

Added files:

- frontend/src/lib/persian-copy.ts
- scripts/audit_frontend_persian_copy.py

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/publishing/queue/page.tsx
- frontend/src/app/settings/page.tsx
- frontend/src/components/create-publishing-queue-item-form.tsx
- frontend/src/components/run-publishing-queue-item-action.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- centralized Persian copy helpers
- visual schematic dashboard flow
- clearer daily operator dashboard
- Persian labels for queue status, attempt status, connectors and run modes
- clearer publishing queue page
- clearer queue form buttons and messages
- frontend copy audit report for remaining English UI copy

Next recommended step:

Use docs/frontend-copy-audit.md to polish remaining WordPress, Telegram, variants and attempt pages.
    ''',
)


rewrite_frontend_check()

print("Release Pack AI-1 applied successfully.")
