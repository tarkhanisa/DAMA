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
    "frontend/src/lib/operator-workflow.ts",
    r'''
export type OperatorSignal = {
  wordpressReady: boolean;
  telegramReady: boolean;
  variantCount: number;
  readyVariantCount: number;
  queueCount: number;
  queuedCount: number;
  failedQueueCount: number;
  attemptCount: number;
  failedAttemptCount: number;
  latestAttemptStatus: string;
};

export type OperatorChecklistItem = {
  step: number;
  title: string;
  description: string;
  href: string;
  actionLabel: string;
  state: "done" | "active" | "pending" | "warning";
};

export function buildOperatorChecklist(signal: OperatorSignal): OperatorChecklistItem[] {
  const connectorReady = signal.wordpressReady || signal.telegramReady;

  return [
    {
      step: 1,
      title: "اتصال‌ها را آماده کن",
      description: connectorReady
        ? "حداقل یکی از اتصال‌های وردپرس یا تلگرام آماده است."
        : "قبل از انتشار، وضعیت وردپرس یا تلگرام را بررسی کن.",
      href: "/settings",
      actionLabel: "بررسی تنظیمات",
      state: connectorReady ? "done" : "active"
    },
    {
      step: 2,
      title: "محتوا تولید کن",
      description: signal.variantCount > 0
        ? "نسخه‌هایی برای انتشار ساخته شده‌اند."
        : "یک متن مادر بساز یا محتوای آماده را وارد کن.",
      href: "/generate",
      actionLabel: "تولید محتوا",
      state: signal.variantCount > 0 ? "done" : connectorReady ? "active" : "pending"
    },
    {
      step: 3,
      title: "نسخه کانالی را آماده کن",
      description: signal.readyVariantCount > 0
        ? "حداقل یک نسخه آماده انتشار وجود دارد."
        : "برای وردپرس یا تلگرام نسخه کانالی بساز و تأیید کن.",
      href: "/publishing/variants",
      actionLabel: "رفتن به نسخه‌ها",
      state: signal.readyVariantCount > 0 ? "done" : signal.variantCount > 0 ? "active" : "pending"
    },
    {
      step: 4,
      title: "به صف انتشار اضافه کن",
      description: signal.queueCount > 0
        ? "آیتم‌هایی در صف انتشار ثبت شده‌اند."
        : "نسخه تأییدشده را وارد صف انتشار کن.",
      href: "/publishing/queue",
      actionLabel: "مدیریت صف",
      state: signal.queueCount > 0 ? "done" : signal.readyVariantCount > 0 ? "active" : "pending"
    },
    {
      step: 5,
      title: "اجرا و گزارش را بررسی کن",
      description: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "چند مورد نیازمند بررسی وجود دارد."
        : signal.attemptCount > 0
          ? "گزارش‌های اجرا ثبت شده‌اند."
          : "اول اجرای آزمایشی امن را انجام بده و نتیجه را ببین.",
      href: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "/publishing/attempts"
        : "/publishing/queue",
      actionLabel: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "بررسی خطاها"
        : signal.attemptCount > 0
          ? "دیدن گزارش‌ها"
          : "اجرای آزمایشی",
      state: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "warning"
        : signal.attemptCount > 0
          ? "done"
          : signal.queueCount > 0
            ? "active"
            : "pending"
    }
  ];
}

export function getOperatorNextAction(signal: OperatorSignal): OperatorChecklistItem {
  const checklist = buildOperatorChecklist(signal);

  return (
    checklist.find((item) => item.state === "warning") ??
    checklist.find((item) => item.state === "active") ??
    checklist[checklist.length - 1]
  );
}
    ''',
)


write_file(
    "frontend/src/components/operator-checklist.tsx",
    r'''
import type { OperatorChecklistItem } from "../lib/operator-workflow";

type OperatorChecklistProps = {
  items: OperatorChecklistItem[];
  nextAction: OperatorChecklistItem;
};

function stateLabel(state: OperatorChecklistItem["state"]): string {
  if (state === "done") {
    return "انجام شده";
  }

  if (state === "active") {
    return "قدم فعلی";
  }

  if (state === "warning") {
    return "نیازمند بررسی";
  }

  return "بعداً";
}

export function OperatorChecklist({ items, nextAction }: OperatorChecklistProps) {
  return (
    <section className="operator-checklist-panel">
      <div className="next-action-card">
        <div>
          <p className="eyebrow">قدم بعدی پیشنهادی</p>
          <h2>{nextAction.title}</h2>
          <p>{nextAction.description}</p>
        </div>

        <a href={nextAction.href}>{nextAction.actionLabel}</a>
      </div>

      <div className="operator-checklist">
        {items.map((item) => (
          <a
            key={item.step}
            className={`checklist-item checklist-${item.state}`}
            href={item.href}
          >
            <span className="checklist-step">{item.step}</span>
            <div>
              <strong>{item.title}</strong>
              <p>{item.description}</p>
            </div>
            <em>{stateLabel(item.state)}</em>
          </a>
        ))}
      </div>
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/app/page.tsx",
    r'''
import { OperatorChecklist } from "../components/operator-checklist";
import { PageHeader } from "../components/page-header";
import { StatCard } from "../components/stat-card";
import { labelAttemptStatus, labelQueueStatus, labelReady } from "../lib/persian-copy";
import {
  buildOperatorChecklist,
  getOperatorNextAction,
  type OperatorSignal
} from "../lib/operator-workflow";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type RuntimeItem = Record<string, unknown>;

function asRecord(value: unknown): RuntimeItem {
  return value !== null && typeof value === "object" ? (value as RuntimeItem) : {};
}

function getItems(payload: unknown): RuntimeItem[] {
  const record = asRecord(payload);
  const items = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return items.map(asRecord);
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

function itemStatus(item: RuntimeItem): string {
  return String(item.status ?? "").trim();
}

export default async function HomePage() {
  const [wordpressConfig, telegramConfig, variantsPayload, queuePayload, attemptsPayload] =
    await Promise.all([
      loadJson("/publishing/wordpress/config"),
      loadJson("/publishing/telegram/config"),
      loadJson("/publishing/variants"),
      loadJson("/publishing/queue"),
      loadJson("/publishing/attempts")
    ]);

  const wordpressReady = Boolean(asRecord(wordpressConfig).ready);
  const telegramReady = Boolean(asRecord(telegramConfig).ready);
  const variants = getItems(variantsPayload);
  const queueItems = getItems(queuePayload);
  const attempts = getItems(attemptsPayload);

  const readyVariantCount = variants.filter((item) =>
    ["approved", "ready_for_publish", "scheduled"].includes(itemStatus(item))
  ).length;

  const queuedCount = queueItems.filter((item) => itemStatus(item) === "queued").length;
  const failedQueueCount = queueItems.filter((item) =>
    ["failed", "blocked"].includes(itemStatus(item))
  ).length;

  const failedAttemptCount = attempts.filter((item) =>
    ["failed", "blocked"].includes(itemStatus(item))
  ).length;

  const latestQueueStatus = labelQueueStatus(String(queueItems[0]?.status ?? ""));
  const latestAttemptStatus = labelAttemptStatus(String(attempts[0]?.status ?? ""));

  const signal: OperatorSignal = {
    wordpressReady,
    telegramReady,
    variantCount: variants.length,
    readyVariantCount,
    queueCount: queueItems.length,
    queuedCount,
    failedQueueCount,
    attemptCount: attempts.length,
    failedAttemptCount,
    latestAttemptStatus: String(attempts[0]?.status ?? "")
  };

  const checklist = buildOperatorChecklist(signal);
  const nextAction = getOperatorNextAction(signal);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="DAMA"
        title="داشبورد راهنمای عملیات محتوا"
        lead="این صفحه به تو می‌گوید الان قدم بعدی چیست؛ از تولید محتوا تا صف انتشار و بررسی گزارش."
      >
        <div className="actions">
          <a href={nextAction.href}>{nextAction.actionLabel}</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">نمای کلی</p>
          <h2>مسیر روزمره DAMA</h2>
          <p>
            مسیر اصلی را از راست به چپ دنبال کن: محتوا بساز، نسخه آماده کن،
            وارد صف کن و نتیجه را بررسی کن.
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

      <OperatorChecklist items={checklist} nextAction={nextAction} />

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
            <p className="eyebrow">راهنمای سریع</p>
            <h2>چطور با کمترین خطا جلو بروم؟</h2>
          </div>

          <ol className="simple-steps">
            <li>اگر قدم پیشنهادی بالا فعال است، همان را انجام بده.</li>
            <li>برای انتشار واقعی عجله نکن؛ اول اجرای آزمایشی امن بزن.</li>
            <li>اگر خطایی دیدی، اول گزارش‌ها و سپس تنظیمات اتصال را بررسی کن.</li>
            <li>برای خلوت نگه‌داشتن پنل، از بخش پیشرفته داده‌های تستی را پاک کن.</li>
          </ol>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">ابزارهای کمتر استفاده‌شده</p>
            <h2>همه چیز جلوی چشم نیست</h2>
          </div>

          <p>
            سلامت سیستم، عملیات، خروجی‌ها، نگهداری و پاک‌سازی داده‌های تستی در بخش
            پیشرفته قرار گرفته‌اند.
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


append_once(
    "frontend/src/app/globals.css",
    "/* Guided operator checklist */",
    r'''
/* Guided operator checklist */
.operator-checklist-panel {
  display: grid;
  gap: 1rem;
  margin: 1.25rem 0;
}

.next-action-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: center;
  padding: 1.25rem;
  border: 1px solid rgba(35, 74, 112, 0.28);
  border-radius: 1.5rem;
  background:
    radial-gradient(circle at top right, rgba(35, 74, 112, 0.13), transparent 34%),
    rgba(255, 255, 255, 0.9);
  box-shadow: var(--shadow);
}

.next-action-card h2 {
  margin: 0.25rem 0 0.5rem;
}

.next-action-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.9;
}

.next-action-card a {
  display: inline-flex;
  min-height: 2.75rem;
  align-items: center;
  justify-content: center;
  padding: 0 1rem;
  border-radius: 999px;
  background: var(--text);
  color: white;
  text-decoration: none;
  font-weight: 900;
}

.operator-checklist {
  display: grid;
  gap: 0.7rem;
}

.checklist-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.8rem;
  align-items: center;
  padding: 0.95rem 1rem;
  border: 1px solid var(--border);
  border-radius: 1.15rem;
  background: rgba(255, 255, 255, 0.68);
  color: var(--text);
  text-decoration: none;
}

.checklist-item strong {
  display: block;
  margin-bottom: 0.25rem;
}

.checklist-item p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.checklist-item em {
  font-style: normal;
  color: var(--muted);
  font-weight: 800;
}

.checklist-step {
  display: inline-flex;
  width: 2.15rem;
  height: 2.15rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(16, 25, 39, 0.08);
  font-weight: 900;
}

.checklist-done {
  opacity: 0.82;
}

.checklist-active {
  border-color: rgba(35, 74, 112, 0.36);
  background: rgba(255, 255, 255, 0.95);
}

.checklist-warning {
  border-color: rgba(160, 80, 40, 0.35);
  background: rgba(255, 248, 242, 0.95);
}

.checklist-pending {
  opacity: 0.68;
}

@media (max-width: 720px) {
  .next-action-card,
  .checklist-item {
    grid-template-columns: 1fr;
  }

  .next-action-card a {
    width: 100%;
  }
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
    ".\frontend\src\lib\operator-workflow.ts",
    ".\frontend\src\components\operator-checklist.tsx",
    ".\frontend\src\components\cleanup-test-data-action.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx",
    ".\frontend\src\app\advanced\cleanup\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$OperatorWorkflow = Read-TextFile ".\frontend\src\lib\operator-workflow.ts"
$OperatorChecklist = Read-TextFile ".\frontend\src\components\operator-checklist.tsx"
$QueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$AttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"
$AttemptDetailPage = Read-TextFile ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx"
$CleanupPage = Read-TextFile ".\frontend\src\app\advanced\cleanup\page.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($OperatorWorkflow -notmatch "buildOperatorChecklist") {
    throw "Operator workflow helper is missing checklist builder."
}

if ($OperatorWorkflow -notmatch "getOperatorNextAction") {
    throw "Operator workflow helper is missing next action resolver."
}

if ($OperatorChecklist -notmatch "next-action-card") {
    throw "Operator checklist component is missing next action card."
}

if ($HomePage -notmatch "OperatorChecklist") {
    throw "Home page is not rendering operator checklist."
}

if ($HomePage -notmatch "getOperatorNextAction") {
    throw "Home page is not using next action resolver."
}

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

if ($CleanupPage -notmatch "/publishing/cleanup/test-data/preview") {
    throw "Cleanup page does not call cleanup preview endpoint."
}

if ($Styles -notmatch "Guided operator checklist") {
    throw "Global styles are missing guided operator checklist marker."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-4 Completed",
    r'''
## Release Pack AI-4 Completed

Name:

Guided Operator Checklist

Added files:

- frontend/src/lib/operator-workflow.ts
- frontend/src/components/operator-checklist.tsx

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- guided operator checklist on dashboard
- automatic next action suggestion
- dashboard now reads connector, variant, queue and attempt status
- clear five-step daily workflow
- warning state when queue or attempts need review
- simpler operator console behavior before adding bigger multi-channel dashboard

Next recommended step:

Release Pack AI-5: Variants Page Persian Polish

Goal:

- simplify and Persian-polish the variants page
- make review/approval flow clearer
- add "send to queue" path from variant detail
    ''',
)


print("Release Pack AI-4 applied successfully.")
