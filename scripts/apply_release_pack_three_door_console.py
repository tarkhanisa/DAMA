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
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/produce", label: "تولید" },
  { href: "/publishing", label: "انتشار" },
  { href: "/other", label: "سایر" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="ناوبری اصلی DAMA">
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


write_file(
    "frontend/src/app/page.tsx",
    r'''
import { PageHeader } from "../components/page-header";

export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="DAMA"
        title="چه کاری میخواهی انجام بدهی"
        lead="برای سادهتر شدن کار پنل به سه بخش اصلی تقسیم شده است: تولید انتشار و سایر."
      />

      <section className="three-door-console" aria-label="درهای اصلی پنل">
        <a className="door-card door-primary" href="/produce">
          <span></span>
          <strong>تولید</strong>
          <p>متن ایده پست تصویر یا ویدیو را برای یک پروژه آماده کن.</p>
          <em>شروع تولید محتوا</em>
        </a>

        <a className="door-card door-primary" href="/publishing">
          <span></span>
          <strong>انتشار</strong>
          <p>پروژه را انتخاب کن متن و رسانه را وارد کن کانالها را انتخاب کن و برای انتشار آماده شو.</p>
          <em>شروع انتشار</em>
        </a>

        <a className="door-card" href="/other">
          <span></span>
          <strong>سایر</strong>
          <p>گزارشها تنظیمات تاریخچه پشتیبان پاکسازی و ابزارهای فنی.</p>
          <em>رفتن به ابزارها</em>
        </a>
      </section>

      <section className="panel quiet-panel">
        <div className="panel-heading">
          <p className="eyebrow">مسیر پیشنهادی</p>
          <h2>برای کار روزمره</h2>
        </div>

        <ol className="simple-steps">
          <li>اگر میخواهی چیزی بسازی از تولید شروع کن.</li>
          <li>اگر محتوایت آماده است و میخواهی منتشر کنی از انتشار شروع کن.</li>
          <li>اگر میخواهی گزارشها تنظیمات یا پاکسازی را ببینی برو به سایر.</li>
        </ol>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/produce/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function ProducePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید"
        title="برای چه پروژهای میخواهی محتوا بسازی"
        lead="این بخش فعلا مسیر ساده تولید متن و پست را نگه میدارد. تولید تصویر و ویدیو در مرحلههای بعدی توسعه پیدا میکند."
      >
        <div className="actions">
          <a href="/generate">تولید متن</a>
          <a href="/projects">پروژهها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="متن و پست" value="فعال" helper="با موتور فعلی تولید محتوا" />
        <StatCard label="تصویر" value="بعدی" helper="در فاز تولید رسانه" />
        <StatCard label="ویدیو" value="بعدی" helper="در فاز تولید رسانه" />
        <StatCard label="پروژه" value="محور اصلی" helper="هر تولید باید به پروژه وصل شود" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/generate">
          <span></span>
          <strong>تولید متن / پست</strong>
          <p>برای سایت تلگرام لینکدین یا کمپین متن مادر بساز.</p>
        </a>

        <a className="operator-card" href="/projects">
          <span></span>
          <strong>انتخاب یا بررسی پروژه</strong>
          <p>پروژههایی که قبلا تعریف شدهاند را ببین.</p>
        </a>

        <a className="operator-card muted-operator-card" href="/produce">
          <span></span>
          <strong>تولید تصویر</strong>
          <p>در مرحله بعد تولید تصویر پروژهمحور از اینجا فعال میشود.</p>
        </a>

        <a className="operator-card muted-operator-card" href="/produce">
          <span></span>
          <strong>تولید ویدیو</strong>
          <p>در مرحلههای بعد تولید ویدیو و آمادهسازی رسانه اضافه میشود.</p>
        </a>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/components/simple-publish-wizard-form.tsx",
    r'''
"use client";

import { FormEvent, useMemo, useState } from "react";
import { friendlyErrorMessage, labelConnector } from "../lib/persian-copy";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
};

type SimplePublishWizardFormProps = {
  apiBaseUrl: string;
  channels: ChannelOption[];
};

export function SimplePublishWizardForm({
  apiBaseUrl,
  channels
}: SimplePublishWizardFormProps) {
  const defaultChannelIds = useMemo(
    () => channels.filter((channel) => ["wordpress", "telegram"].includes(channel.channel_type)).map((channel) => channel.id),
    [channels]
  );

  const [projectName, setProjectName] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceBody, setSourceBody] = useState("");
  const [mediaUrls, setMediaUrls] = useState("");
  const [selectedChannelIds, setSelectedChannelIds] = useState<string[]>(defaultChannelIds);
  const [message, setMessage] = useState("");
  const [campaignLink, setCampaignLink] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  function toggleChannel(channelId: string) {
    setSelectedChannelIds((current) =>
      current.includes(channelId)
        ? current.filter((item) => item !== channelId)
        : [...current, channelId]
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");
    setCampaignLink("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/campaigns`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          source_title: sourceTitle,
          source_body: sourceBody,
          media_urls: mediaUrls,
          channel_ids: selectedChannelIds,
          campaign_goal: "انتشار چندکاناله",
          notes: "created from simplified publish wizard"
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("کمپین انتشار ساخته شد. قدم بعدی: ساخت نسخههای مخصوص هر کانال.");
      setCampaignLink(`/publishing/campaigns/${payload.id}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel publish-wizard-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">شروع انتشار</p>
        <h2>اول پروژه را مشخص کن</h2>
      </div>

      <label>
        این محتوا برای کدام پروژه است
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="مثلا دامامدیا گرگران درخت و دختر اورماشاپ..."
          required
        />
      </label>

      <label>
        عنوان انتشار
        <input
          value={sourceTitle}
          onChange={(event) => setSourceTitle(event.target.value)}
          placeholder="عنوان کوتاه این پست یا کمپین"
          required
        />
      </label>

      <label>
        توضیح اصلی
        <textarea
          value={sourceBody}
          onChange={(event) => setSourceBody(event.target.value)}
          placeholder="توضیح اصلی را اینجا بنویس. بعدا برای هر شبکه نسخه مناسب ساخته میشود."
          rows={7}
          required
        />
      </label>

      <label>
        عکسها یا ویدیوها
        <textarea
          value={mediaUrls}
          onChange={(event) => setMediaUrls(event.target.value)}
          placeholder="هر مسیر فایل یا لینک را در یک خط بگذار. مثال: I:\DAMA\media\poster.jpg"
          rows={4}
        />
      </label>

      <div className="field-group">
        <span>کجا منتشر شود</span>

        <div className="channel-checkbox-grid">
          {channels.length > 0 ? (
            channels.map((channel) => (
              <label className="checkbox-card" key={channel.id}>
                <input
                  type="checkbox"
                  checked={selectedChannelIds.includes(channel.id)}
                  onChange={() => toggleChannel(channel.id)}
                />
                <strong>{channel.name || labelConnector(channel.channel_type)}</strong>
                <small>{labelConnector(channel.channel_type)}</small>
              </label>
            ))
          ) : (
            <p className="muted-note">هنوز کانال فعالی ثبت نشده است. اول از بخش تنظیمات/انتشار کانالها را بساز.</p>
          )}
        </div>
      </div>

      <p className="muted-note">
        این دکمه هنوز چیزی را منتشر نمیکند. فقط یک کمپین مادر میسازد تا در قدم بعد برای هر کانال نسخه جدا ساخته شود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      {campaignLink ? (
        <div className="actions">
          <a href={campaignLink}>مشاهده کمپین ساختهشده</a>
          <a href="/publishing/campaigns">همه کمپینها</a>
        </div>
      ) : null}

      <button type="submit" disabled={isSaving || !projectName || !sourceTitle || !sourceBody}>
        {isSaving ? "در حال ساخت..." : "ساخت کمپین انتشار"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { SimplePublishWizardForm } from "../../components/simple-publish-wizard-form";
import { StatCard } from "../../components/stat-card";
import { labelConnector } from "../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getItems(payload: unknown): Record<string, unknown>[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return source.map(asRecord);
}

function normalizeChannels(payload: unknown): ChannelOption[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      name: String(item.name ?? ""),
      channel_type: String(item.channel_type ?? ""),
      status: String(item.status ?? "")
    }))
    .filter((item) => item.id)
    .filter((item) => item.status !== "inactive");
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

export default async function PublishingHomePage() {
  const channels = normalizeChannels(await loadJson("/publishing/channels"));

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار"
        title="چه چیزی را برای کدام پروژه منتشر کنیم"
        lead="اول پروژه را مشخص کن بعد متن و رسانه را وارد کن سپس کانالهای مقصد را انتخاب کن."
      >
        <div className="actions">
          <a href="/publishing/campaigns">کمپینهای قبلی</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="قدم فعلی" value="ساخت کمپین" helper="هنوز انتشار واقعی انجام نمیشود" />
        <StatCard label="کانالهای فعال" value={channels.length} helper="قابل انتخاب برای کمپین" />
        <StatCard label="مرحله بعد" value="نسخهسازی" helper="برای هر کانال متن جدا ساخته میشود" />
        <StatCard label="انتشار" value="دستی" helper="بعد از بازبینی و صف انتشار" />
      </section>

      <section className="publish-flow-strip" aria-label="مسیر انتشار">
        <div>
          <span></span>
          <strong>پروژه</strong>
        </div>
        <div>
          <span></span>
          <strong>متن و رسانه</strong>
        </div>
        <div>
          <span></span>
          <strong>کانالها</strong>
        </div>
        <div>
          <span></span>
          <strong>نسخهسازی</strong>
        </div>
        <div>
          <span></span>
          <strong>صف انتشار</strong>
        </div>
      </section>

      <section className="two-column">
        <SimplePublishWizardForm apiBaseUrl={API_BASE_URL} channels={channels} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">کانالهای فعلی</p>
            <h2>مقصدهای قابل انتخاب</h2>
          </div>

          <div className="channel-chip-list">
            {channels.length > 0 ? (
              channels.map((channel) => (
                <span className="channel-chip" key={channel.id}>
                  {channel.name || labelConnector(channel.channel_type)}
                  <small>{labelConnector(channel.channel_type)}</small>
                </span>
              ))
            ) : (
              <p className="muted-note">هنوز کانالی ثبت نشده است.</p>
            )}
          </div>

          <div className="actions">
            <a href="/publishing/campaigns">کمپینها</a>
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
    "frontend/src/app/other/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";

export const dynamic = "force-dynamic";

const groups = [
  {
    title: "گزارش و تاریخچه",
    items: [
      {
        href: "/publishing/attempts",
        title: "گزارش انتشار",
        description: "نتیجه اجرای وردپرس تلگرام dry-run و خطاها."
      },
      {
        href: "/publishing/campaigns",
        title: "کمپینهای قبلی",
        description: "کمپینهایی که برای انتشار ساخته شدهاند."
      },
      {
        href: "/publishing/queue",
        title: "صف انتشار",
        description: "آیتمهایی که برای اجرا آماده شدهاند."
      }
    ]
  },
  {
    title: "تنظیمات و نگهداری",
    items: [
      {
        href: "/settings",
        title: "تنظیمات اتصال",
        description: "وضعیت وردپرس و تلگرام."
      },
      {
        href: "/advanced/cleanup",
        title: "پاکسازی دادههای تستی",
        description: "حذف امن دادههای smoke/test با backup."
      },
      {
        href: "/maintenance",
        title: "نگهداری",
        description: "ابزارهای نگهداری سیستم."
      }
    ]
  },
  {
    title: "ابزارهای فنی",
    items: [
      {
        href: "/advanced",
        title: "پیشرفته",
        description: "همه ابزارهای کماستفاده و فنی."
      },
      {
        href: "/runtime",
        title: "سلامت سیستم",
        description: "بررسی وضعیت backend و سرویسها."
      },
      {
        href: "/projects",
        title: "پروژهها",
        description: "فهرست و مدیریت پروژهها."
      },
      {
        href: "/content-assets",
        title: "محتواها",
        description: "داراییهای محتوایی ثبتشده."
      }
    ]
  }
];

export default function OtherPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="سایر"
        title="گزارشها تنظیمات و ابزارهای فنی"
        lead="هر چیزی که کار روزمره تولید و انتشار نیست اینجا قرار میگیرد تا داشبورد اصلی شلوغ نشود."
      >
        <div className="actions">
          <a href="/">داشبورد</a>
          <a href="/advanced">پیشرفته</a>
        </div>
      </PageHeader>

      <section className="other-groups">
        {groups.map((group) => (
          <section className="panel" key={group.title}>
            <div className="panel-heading">
              <p className="eyebrow">سایر</p>
              <h2>{group.title}</h2>
            </div>

            <div className="operator-grid">
              {group.items.map((item) => (
                <a className="operator-card" href={item.href} key={item.href}>
                  <span></span>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </a>
              ))}
            </div>
          </section>
        ))}
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Three door operator console */",
    r'''
/* Three door operator console */
.three-door-console {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}

.door-card {
  display: grid;
  gap: 0.9rem;
  align-content: start;
  min-height: 17rem;
  padding: 1.45rem;
  border: 1px solid var(--border);
  border-radius: 1.7rem;
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  text-decoration: none;
  box-shadow: var(--shadow);
}

.door-card span {
  display: inline-flex;
  width: 2.5rem;
  height: 2.5rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(16, 25, 39, 0.08);
  font-weight: 900;
}

.door-card strong {
  font-size: 1.45rem;
}

.door-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.9;
}

.door-card em {
  margin-top: auto;
  font-style: normal;
  font-weight: 900;
}

.door-primary {
  border-color: rgba(35, 74, 112, 0.34);
  background:
    radial-gradient(circle at top right, rgba(35, 74, 112, 0.12), transparent 34%),
    rgba(255, 255, 255, 0.88);
}

.muted-operator-card {
  opacity: 0.66;
}

.publish-wizard-form {
  border-color: rgba(35, 74, 112, 0.24);
}

.publish-flow-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.7rem;
  margin: 1.25rem 0;
}

.publish-flow-strip div {
  display: grid;
  gap: 0.4rem;
  justify-items: center;
  padding: 0.9rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.62);
  text-align: center;
}

.publish-flow-strip span {
  display: inline-flex;
  width: 2rem;
  height: 2rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(16, 25, 39, 0.08);
  font-weight: 900;
}

.publish-flow-strip strong {
  font-size: 0.95rem;
}

.other-groups {
  display: grid;
  gap: 1rem;
}

@media (max-width: 980px) {
  .three-door-console,
  .publish-flow-strip {
    grid-template-columns: 1fr;
  }

  .door-card {
    min-height: auto;
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
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\simple-publish-wizard-form.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\produce\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\other\page.tsx",
    ".\frontend\src\app\publishing\campaigns\page.tsx",
    ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$ProducePage = Read-TextFile ".\frontend\src\app\produce\page.tsx"
$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$OtherPage = Read-TextFile ".\frontend\src\app\other\page.tsx"
$PublishWizard = Read-TextFile ".\frontend\src\components\simple-publish-wizard-form.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

$ExpectedTopRoutes = @(
    'href: "/"',
    'href: "/produce"',
    'href: "/publishing"',
    'href: "/other"'
)

foreach ($Route in $ExpectedTopRoutes) {
    if ($AppNav -notmatch [regex]::Escape($Route)) {
        throw "Main nav missing route: $Route"
    }
}

if ($HomePage -notmatch "three-door-console") {
    throw "Home page is missing three-door console."
}

if ($ProducePage -notmatch "/generate") {
    throw "Produce page does not link to generation."
}

if ($PublishingPage -notmatch "SimplePublishWizardForm") {
    throw "Publishing page is missing simplified publish wizard."
}

if ($PublishWizard -notmatch "/publishing/campaigns") {
    throw "Publish wizard does not create campaigns."
}

if ($PublishWizard -notmatch "channel_ids") {
    throw "Publish wizard does not submit selected channels."
}

if ($OtherPage -notmatch "/advanced/cleanup") {
    throw "Other page does not link to cleanup."
}

if ($OtherPage -notmatch "/publishing/attempts") {
    throw "Other page does not link to publishing attempts."
}

if ($Styles -notmatch "Three door operator console") {
    throw "Global styles missing three-door marker."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-6 Completed",
    r'''
## Release Pack AI-6 Completed

Name:

Three-Door Operator Console + Publish Wizard

Added files:

- frontend/src/app/produce/page.tsx
- frontend/src/app/other/page.tsx
- frontend/src/components/simple-publish-wizard-form.tsx

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/publishing/page.tsx
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- dashboard reduced to three main doors: Produce, Publish, Other
- production area separated from publishing
- publishing starts with project/context question
- publishing wizard creates a media campaign
- reports, settings, cleanup, backups and technical tools moved to Other
- top navigation simplified dramatically

Next recommended step:

Release Pack AI-7: Campaign-to-Variants Planner

Goal:

- after a campaign is created, generate platform-specific variants for selected channels
- link generated variants back to the campaign
- then add those variants to the publishing queue
    ''',
)


print("Release Pack AI-6 applied successfully.")
