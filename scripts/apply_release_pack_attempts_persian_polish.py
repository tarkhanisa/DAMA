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

export function labelBoolean(value: boolean | undefined | null): string {
  return value ? "بله" : "خیر";
}

export function shortId(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  if (text.length <= 10) {
    return text;
  }

  return `${text.slice(0, 6)}${text.slice(-4)}`;
}

export function formatPersianDate(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  const date = new Date(text);

  if (Number.isNaN(date.getTime())) {
    return text;
  }

  return date.toLocaleString("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}

export function friendlyErrorMessage(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  const lowered = text.toLowerCase();

  if (lowered.includes("failed to fetch") || lowered.includes("fetch")) {
    return "ارتباط با سرور برقرار نشد.";
  }

  if (text.includes("HTTP 404")) {
    return "مسیر موردنظر پیدا نشد.";
  }

  if (text.includes("HTTP 500")) {
    return "خطای داخلی سرور رخ داد.";
  }

  if (lowered.includes("timeout") || lowered.includes("timed out")) {
    return "زمان اتصال تمام شد. اتصال اینترنت یا VPN را بررسی کن.";
  }

  if (lowered.includes("telegram")) {
    return "اتصال یا ارسال تلگرام نیازمند بررسی است.";
  }

  if (lowered.includes("wordpress")) {
    return "اتصال یا ساخت پیش‌نویس وردپرس نیازمند بررسی است.";
  }

  return text;
}

export function attemptResultSummary(status: string | undefined | null): string {
  const key = String(status ?? "").trim();

  if (key === "draft_created") {
    return "پیش‌نویس وردپرس با موفقیت ساخته شده است.";
  }

  if (key === "test_sent") {
    return "پیام تست تلگرام با موفقیت ارسال شده است.";
  }

  if (key === "dry_run") {
    return "اجرای آزمایشی انجام شده و چیزی واقعاً منتشر نشده است.";
  }

  if (key === "failed") {
    return "این اجرا ناموفق بوده و باید جزئیات بررسی شود.";
  }

  if (key === "blocked") {
    return "این اجرا به‌دلیل ناقص‌بودن تنظیمات یا شرط ایمنی متوقف شده است.";
  }

  return "نتیجه این اجرا در جزئیات ثبت شده است.";
}
    ''',
)


write_file(
    "frontend/src/app/publishing/attempts/page.tsx",
    r'''
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import {
  attemptResultSummary,
  formatPersianDate,
  friendlyErrorMessage,
  labelAttemptStatus,
  labelConnector,
  labelMode,
  shortId
} from "../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingAttempt = {
  id: string;
  connector: string;
  mode: string;
  status: string;
  variant_id: string;
  channel_name: string;
  channel_type: string;
  created_at: string;
  updated_at: string;
  error: string;
  target_url: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeAttempts(payload: unknown): PublishingAttempt[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];

  return source
    .map((item) => {
      const value = asRecord(item);
      const request = asRecord(value.request);
      const response = asRecord(value.response);

      return {
        id: String(value.id ?? ""),
        connector: String(value.connector ?? value.channel_type ?? request.connector ?? ""),
        mode: String(value.mode ?? request.mode ?? ""),
        status: String(value.status ?? ""),
        variant_id: String(value.variant_id ?? request.variant_id ?? ""),
        channel_name: String(value.channel_name ?? request.channel_name ?? response.channel_name ?? ""),
        channel_type: String(value.channel_type ?? request.channel_type ?? ""),
        created_at: String(value.created_at ?? value.createdAt ?? ""),
        updated_at: String(value.updated_at ?? value.updatedAt ?? ""),
        error: String(value.error ?? response.error ?? ""),
        target_url: String(value.target_url ?? request.target_url ?? response.target_url ?? "")
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

export default async function PublishingAttemptsPage() {
  const attempts = await loadAttempts();

  const successfulCount = attempts.filter((item) =>
    ["draft_created", "test_sent", "dry_run"].includes(item.status)
  ).length;

  const failedCount = attempts.filter((item) =>
    ["failed", "blocked"].includes(item.status)
  ).length;

  const latestAttempt = attempts[0];

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="گزارش‌ها"
        title="گزارش اجرای انتشار"
        lead="هر بار که وردپرس، تلگرام یا اجرای آزمایشی را اجرا می‌کنی، نتیجه اینجا ثبت می‌شود."
      >
        <div className="actions">
          <a href="/publishing/queue">صف انتشار</a>
          <a href="/publishing">مرکز انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کل گزارش‌ها" value={attempts.length} helper="همه اجراهای ثبت‌شده" />
        <StatCard label="موفق / آزمایشی" value={successfulCount} helper="بدون خطای جدی" />
        <StatCard label="نیازمند بررسی" value={failedCount} helper="خطا یا توقف ایمنی" />
        <StatCard
          label="آخرین نتیجه"
          value={latestAttempt ? labelAttemptStatus(latestAttempt.status) : ""}
          helper={latestAttempt ? attemptResultSummary(latestAttempt.status) : "هنوز گزارشی ثبت نشده"}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست گزارش‌ها</p>
          <h2>آخرین اجراها</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>نتیجه</th>
                <th>مقصد</th>
                <th>نوع اجرا</th>
                <th>زمان</th>
                <th>خطا</th>
                <th>جزئیات</th>
              </tr>
            </thead>
            <tbody>
              {attempts.length > 0 ? (
                attempts.slice(0, 80).map((attempt) => (
                  <tr key={attempt.id}>
                    <td>
                      <span className={`status-badge status-${attempt.status}`}>
                        {labelAttemptStatus(attempt.status)}
                      </span>
                    </td>
                    <td>{labelConnector(attempt.connector || attempt.channel_type)}</td>
                    <td>{labelMode(attempt.mode || attempt.connector)}</td>
                    <td>{formatPersianDate(attempt.created_at)}</td>
                    <td>{attempt.error ? friendlyErrorMessage(attempt.error) : ""}</td>
                    <td>
                      <a href={`/publishing/attempts/${attempt.id}`}>
                        مشاهده جزئیات {shortId(attempt.id)}
                      </a>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>فعلاً گزارشی ثبت نشده است.</td>
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
import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";
import {
  attemptResultSummary,
  formatPersianDate,
  friendlyErrorMessage,
  labelAttemptStatus,
  labelConnector,
  labelMode,
  shortId
} from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type Props = {
  params: Promise<{
    attemptId: string;
  }>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function stringFrom(...values: unknown[]): string {
  for (const value of values) {
    const text = String(value ?? "").trim();

    if (text) {
      return text;
    }
  }

  return "";
}

async function loadAttempt(attemptId: string): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/attempts/${attemptId}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return asRecord(await response.json());
  } catch {
    return {};
  }
}

export default async function PublishingAttemptDetailPage({ params }: Props) {
  const { attemptId } = await params;
  const attempt = await loadAttempt(attemptId);

  const request = asRecord(attempt.request);
  const response = asRecord(attempt.response);

  const status = stringFrom(attempt.status, response.status);
  const connector = stringFrom(attempt.connector, attempt.channel_type, request.connector);
  const mode = stringFrom(attempt.mode, request.mode, connector);
  const createdAt = stringFrom(attempt.created_at, attempt.createdAt);
  const error = stringFrom(attempt.error, response.error);
  const variantId = stringFrom(attempt.variant_id, request.variant_id);
  const targetUrl = stringFrom(attempt.target_url, request.target_url, response.target_url);
  const externalUrl = stringFrom(
    response.draft_url,
    response.wordpress_draft_url,
    response.link,
    response.url,
    response.external_url
  );
  const externalId = stringFrom(
    response.wordpress_post_id,
    response.post_id,
    response.telegram_message_id,
    response.message_id
  );

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="جزئیات گزارش"
        title={`گزارش اجرا ${shortId(attemptId)}`}
        lead={attemptResultSummary(status)}
      >
        <div className="actions">
          <a href="/publishing/attempts">بازگشت به گزارش‌ها</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="نتیجه" value={labelAttemptStatus(status)} helper={error ? friendlyErrorMessage(error) : "بدون خطای ثبت‌شده"} />
        <StatCard label="مقصد" value={labelConnector(connector)} helper={targetUrl || ""} />
        <StatCard label="نوع اجرا" value={labelMode(mode)} helper={variantId ? `نسخه: ${shortId(variantId)}` : ""} />
        <StatCard label="زمان اجرا" value={formatPersianDate(createdAt)} helper={`شناسه: ${shortId(attemptId)}`} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">خلاصه ساده</p>
            <h2>چه اتفاقی افتاد؟</h2>
          </div>

          <dl className="detail-list">
            <div>
              <dt>وضعیت</dt>
              <dd>{labelAttemptStatus(status)}</dd>
            </div>
            <div>
              <dt>مقصد</dt>
              <dd>{labelConnector(connector)}</dd>
            </div>
            <div>
              <dt>نوع اجرا</dt>
              <dd>{labelMode(mode)}</dd>
            </div>
            <div>
              <dt>شناسه خروجی</dt>
              <dd>{externalId || ""}</dd>
            </div>
            <div>
              <dt>خطا</dt>
              <dd>{error ? friendlyErrorMessage(error) : ""}</dd>
            </div>
          </dl>

          {externalUrl ? (
            <div className="actions">
              <a href={externalUrl} target="_blank" rel="noreferrer">
                باز کردن خروجی
              </a>
            </div>
          ) : null}
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>بعدش چه کنم؟</h2>
          </div>

          <ol className="simple-steps">
            <li>اگر نتیجه موفق است، خروجی را در مقصد بررسی کن.</li>
            <li>اگر اجرای آزمایشی بوده، می‌توانی اجرای واقعی را از صف انجام بدهی.</li>
            <li>اگر خطا دارد، اول تنظیمات اتصال و اینترنت/VPN را بررسی کن.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی</summary>
          <p className="muted-note">
            این بخش برای عیب‌یابی است. در استفاده روزمره معمولاً نیازی به آن نداری.
          </p>
          <pre className="json-block">{JSON.stringify(attempt, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Persian attempts polish */",
    r'''
/* Persian attempts polish */
.detail-list {
  display: grid;
  gap: 0.75rem;
  margin: 0;
}

.detail-list div {
  display: grid;
  grid-template-columns: minmax(120px, 0.35fr) 1fr;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
}

.detail-list dt {
  color: var(--muted);
  font-weight: 800;
}

.detail-list dd {
  margin: 0;
  color: var(--text);
  line-height: 1.8;
}

.technical-details {
  border: 1px dashed var(--border);
  border-radius: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.45);
}

.technical-details summary {
  cursor: pointer;
  font-weight: 900;
}

@media (max-width: 720px) {
  .detail-list div {
    grid-template-columns: 1fr;
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
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx",
    ".\frontend\src\app\settings\page.tsx",
    ".\frontend\src\app\advanced\page.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$PersianCopy = Read-TextFile ".\frontend\src\lib\persian-copy.ts"
$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$QueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$AttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"
$AttemptDetailPage = Read-TextFile ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx"

if ($PersianCopy -notmatch "labelAttemptStatus") {
    throw "Persian copy helper is missing attempt status labels."
}

if ($PersianCopy -notmatch "attemptResultSummary") {
    throw "Persian copy helper is missing attempt result summary."
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

if ($AttemptDetailPage -notmatch "نمایش جزئیات فنی") {
    throw "Attempt detail page is missing Persian technical details label."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-2 Completed",
    r'''
## Release Pack AI-2 Completed

Name:

Persian Attempts & Technical Details Polish

Updated files:

- frontend/src/lib/persian-copy.ts
- frontend/src/app/publishing/attempts/page.tsx
- frontend/src/app/publishing/attempts/[attemptId]/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- Persian labels for publishing attempts
- simplified attempts list
- simplified attempt detail page
- technical JSON moved behind collapsible details
- better Persian error summaries
- safer frontend check using LiteralPath for dynamic route folders

Next recommended step:

Release Pack AI-3: Smart Test Data Cleanup

Goal:

- remove only smoke/test queue items, variants and attempts
- preserve clean real WordPress and Telegram channels
- add a button/page in Advanced for safe cleanup
    ''',
)


print("Release Pack AI-2 applied successfully.")
