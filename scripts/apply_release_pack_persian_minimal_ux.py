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


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\advanced\\page.tsx",',
        '".\\frontend\\src\\app\\settings\\page.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\publishing\\queue\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/generate", label: "تولید محتوا" },
  { href: "/publishing", label: "انتشار" },
  { href: "/projects", label: "پروژه‌ها" },
  { href: "/content-assets", label: "محتواها" },
  { href: "/settings", label: "تنظیمات" },
  { href: "/advanced", label: "پیشرفته" }
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
import { StatCard } from "../components/stat-card";

export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="DAMA"
        title="داشبورد ساده عملیات محتوا"
        lead="از اینجا مسیر روزمره را شروع کن: تولید محتوا، آماده‌سازی انتشار، و بررسی نتیجه‌ها."
      >
        <div className="actions">
          <a href="/generate">تولید محتوا</a>
          <a href="/publishing">انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="مسیر اصلی" value="تولید  انتشار" helper="برای کار روزمره" />
        <StatCard label="وردپرس" value="Draft" helper="ساخت پیش‌نویس واقعی" />
        <StatCard label="تلگرام" value="Test Send" helper="ارسال تست واقعی" />
        <StatCard label="صف انتشار" value="دستی" helper="ایمن و قابل کنترل" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/generate">
          <span></span>
          <strong>تولید محتوا</strong>
          <p>متن مادر را بساز یا محتوای آماده را وارد کن.</p>
        </a>

        <a className="operator-card" href="/publishing/variants">
          <span></span>
          <strong>نسخه‌سازی</strong>
          <p>برای وردپرس، تلگرام و کانال‌های دیگر نسخه جدا بساز.</p>
        </a>

        <a className="operator-card" href="/publishing/queue">
          <span></span>
          <strong>صف انتشار</strong>
          <p>نسخه‌های تأییدشده را وارد صف کن و دستی اجرا کن.</p>
        </a>

        <a className="operator-card" href="/publishing/attempts">
          <span></span>
          <strong>گزارش‌ها</strong>
          <p>نتیجه Draft وردپرس، پیام تلگرام و خطاها را ببین.</p>
        </a>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">اصل کار</p>
          <h2>مسیر پیشنهادی روزانه</h2>
        </div>

        <ol className="simple-steps">
          <li>اول محتوا را تولید کن.</li>
          <li>بعد برای کانال‌ها نسخه بساز.</li>
          <li>نسخه را بازبینی و تأیید کن.</li>
          <li>آن را به صف انتشار اضافه کن.</li>
          <li>اول Dry-run بزن؛ بعد اجرای واقعی.</li>
        </ol>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function PublishingHomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار"
        title="مرکز ساده انتشار"
        lead="اینجا فقط مسیرهای اصلی انتشار را می‌بینی. تنظیمات فنی و صفحات کم‌استفاده به بخش پیشرفته منتقل شده‌اند."
      >
        <div className="actions">
          <a href="/publishing/queue">صف انتشار</a>
          <a href="/publishing/attempts">گزارش‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="صف انتشار" value="اصلی" helper="مسیر امن اجرا" />
        <StatCard label="وردپرس" value="Draft" helper="بدون Publish مستقیم" />
        <StatCard label="تلگرام" value="Test" helper="ارسال تست کنترل‌شده" />
        <StatCard label="گزارش‌ها" value="ثبت کامل" helper="هر اجرا یک attempt" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/publishing/queue">
          <span></span>
          <strong>صف انتشار</strong>
          <p>نسخه آماده را وارد صف کن و دستی اجرا کن.</p>
        </a>

        <a className="operator-card" href="/publishing/variants">
          <span></span>
          <strong>نسخه‌ها</strong>
          <p>نسخه‌های مخصوص وردپرس و تلگرام را بساز و بازبینی کن.</p>
        </a>

        <a className="operator-card" href="/publishing/attempts">
          <span></span>
          <strong>گزارش انتشار</strong>
          <p>نتیجه اجرای وردپرس، تلگرام و خطاها را بررسی کن.</p>
        </a>

        <a className="operator-card" href="/settings">
          <span></span>
          <strong>تنظیمات اتصال</strong>
          <p>وضعیت وردپرس و تلگرام را از یک جای ساده ببین.</p>
        </a>
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
    return { ready: false, message: "Backend در دسترس نیست." };
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
        title="تنظیمات ساده اتصال‌ها"
        lead="اینجا فقط وضعیت کلی اتصال‌های مهم را می‌بینی. جزئیات فنی در صفحه خود هر اتصال است."
      >
        <div className="actions">
          <a href="/publishing/wordpress">وردپرس</a>
          <a href="/publishing/telegram">تلگرام</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وردپرس" value={wordpress.ready ? "آماده" : "نیازمند بررسی"} helper={wordpress.message ?? ""} />
        <StatCard label="تلگرام" value={telegram.ready ? "آماده" : "نیازمند بررسی"} helper={telegram.message ?? ""} />
        <StatCard label="حالت امن" value="فعال" helper="Dry-run پیش‌فرض است" />
        <StatCard label="Secretها" value="مخفی" helper="در UI نمایش داده نمی‌شوند" />
      </section>

      <section className="operator-grid">
        <a className="operator-card" href="/publishing/wordpress">
          <span>W</span>
          <strong>وردپرس</strong>
          <p>وضعیت Application Password و ساخت Draft را بررسی کن.</p>
        </a>

        <a className="operator-card" href="/publishing/telegram">
          <span>T</span>
          <strong>تلگرام</strong>
          <p>وضعیت Bot Token و ارسال تست تلگرام را بررسی کن.</p>
        </a>

        <a className="operator-card" href="/advanced">
          <span></span>
          <strong>پیشرفته</strong>
          <p>صفحات فنی، سلامت سیستم و ابزارهای نگهداری.</p>
        </a>
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
        lead="این بخش برای وقتی است که بخواهی وضعیت سیستم، ابزارهای فنی یا خروجی‌ها را بررسی کنی."
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


append_once(
    "frontend/src/app/globals.css",
    "/* Minimal Persian operator UX */",
    r'''
/* Minimal Persian operator UX */
.operator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 1rem;
  margin: 1.25rem 0;
}

.operator-card {
  display: grid;
  gap: 0.55rem;
  align-content: start;
  min-height: 9rem;
  padding: 1.2rem;
  border: 1px solid var(--border);
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  text-decoration: none;
  box-shadow: var(--shadow);
}

.operator-card span {
  display: inline-flex;
  width: 2.1rem;
  height: 2.1rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(16, 25, 39, 0.08);
  font-weight: 900;
}

.operator-card strong {
  font-size: 1.05rem;
}

.operator-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.9;
}

.primary-operator-card {
  border-color: rgba(35, 74, 112, 0.35);
  background: rgba(255, 255, 255, 0.88);
}

.simple-steps {
  margin: 0;
  padding-inline-start: 1.25rem;
  line-height: 2.1;
  color: var(--muted);
}

.app-nav {
  gap: 0.35rem;
}

.app-nav a {
  white-space: nowrap;
}
    ''',
)


write_file(
    "scripts/cleanup_operator_runtime_data.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import shutil


ROOT = Path("I:/DAMA")
DATA_DIR = ROOT / "backend/data"
BACKUP_ROOT = ROOT / "backend/backups/runtime-cleanup"


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def backup_data() -> Path:
    backup_dir = BACKUP_ROOT / now_slug()
    backup_dir.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            target = backup_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    return backup_dir


def create_clean_channels() -> list[dict[str, object]]:
    now = datetime.now(timezone.utc).isoformat()

    return [
        {
            "id": str(uuid4()),
            "name": "وردپرس لوکال دامامدیا",
            "channel_type": "wordpress",
            "target_url": "http://damamedia.local",
            "status": "active",
            "notes": "کانال تمیز برای ساخت Draft در وردپرس لوکال دامامدیا.",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid4()),
            "name": "تلگرام تست دامامدیا",
            "channel_type": "telegram",
            "target_url": "",
            "status": "active",
            "notes": "کانال تمیز برای تست Bot تلگرام. chat_id از env یا فرم گرفته می‌شود.",
            "created_at": now,
            "updated_at": now,
        },
    ]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_data()

    write_json(DATA_DIR / "publishing_channels.json", create_clean_channels())
    write_json(DATA_DIR / "publishing_variants.json", [])
    write_json(DATA_DIR / "publishing_attempts.json", [])
    write_json(DATA_DIR / "publishing_queue.json", [])

    print("Runtime data cleanup completed.")
    print(f"Backup created at: {backup_dir}")
    print("Clean channels recreated:")
    print("- وردپرس لوکال دامامدیا")
    print("- تلگرام تست دامامدیا")


if __name__ == "__main__":
    main()
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-0 Completed",
    r'''
## Release Pack AI-0 Completed

Name:

Persian Minimal Operator UX + Runtime Cleanup

Added files:

- frontend/src/app/settings/page.tsx
- frontend/src/app/advanced/page.tsx
- scripts/cleanup_operator_runtime_data.py

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/app/page.tsx
- frontend/src/app/publishing/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- simplified Persian navigation
- cleaner daily dashboard
- simplified publishing center
- settings page for WordPress and Telegram
- advanced section for technical pages
- safe runtime cleanup script with backup
- clean default WordPress and Telegram channels

Next recommended Release Pack:

Release Pack AI: Multi-channel Publish Dashboard

Suggested scope:

- one central workflow page
- choose content asset
- choose channels
- create variants
- add to queue
- run dry-run batch
    ''',
)


patch_frontend_check()

print("Release Pack AI-0 applied successfully.")
