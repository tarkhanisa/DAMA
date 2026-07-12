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
