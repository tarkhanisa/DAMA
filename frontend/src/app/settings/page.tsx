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
