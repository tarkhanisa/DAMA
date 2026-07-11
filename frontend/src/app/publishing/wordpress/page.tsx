import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { WordPressConnectionTestAction } from "../../../components/wordpress-connection-test-action";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type WordPressConfig = {
  ready: boolean;
  missing: string[];
  base_url_configured: boolean;
  username_configured: boolean;
  application_password_configured: boolean;
  base_url_preview: string;
  rest_posts_endpoint: string;
  rest_me_endpoint: string;
  secrets_redacted: boolean;
  message: string;
};

async function loadConfig(): Promise<WordPressConfig> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/wordpress/config`, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return (await response.json()) as WordPressConfig;
  } catch {
    return {
      ready: false,
      missing: ["backend unreachable"],
      base_url_configured: false,
      username_configured: false,
      application_password_configured: false,
      base_url_preview: "",
      rest_posts_endpoint: "",
      rest_me_endpoint: "",
      secrets_redacted: true,
      message: "WordPress config could not be loaded."
    };
  }
}

export default async function WordPressPublishingPage() {
  const config = await loadConfig();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="وردپرس"
        title="وضعیت اتصال وردپرس"
        lead="اینجا فقط وضعیت اتصال و آمادگی ساخت پیش‌نویس وردپرس را بررسی می‌کنی. انتشار مستقیم هنوز فعال نیست."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="آماده اتصال واقعی" value={config.ready ? "بله" : "نه"} helper="وضعیت env وردپرس" />
        <StatCard label="Base URL" value={config.base_url_configured ? "تنظیم شده" : "نیست"} helper={config.base_url_preview || "—"} />
        <StatCard label="Username" value={config.username_configured ? "تنظیم شده" : "نیست"} helper="مقدار نمایش داده نمی‌شود" />
        <StatCard label="App Password" value={config.application_password_configured ? "تنظیم شده" : "نیست"} helper="secret مخفی است" />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Configuration</p>
            <h2>تنظیمات امن</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>پیام</strong>
              <span>{config.message}</span>
            </div>
            <div>
              <strong>REST Posts</strong>
              <span>{config.rest_posts_endpoint || "—"}</span>
            </div>
            <div>
              <strong>REST Me</strong>
              <span>{config.rest_me_endpoint || "—"}</span>
            </div>
            <div>
              <strong>Missing</strong>
              <span>{config.missing.length ? config.missing.join(", ") : "—"}</span>
            </div>
          </div>
        </section>

        <WordPressConnectionTestAction apiBaseUrl={API_BASE_URL} />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">راهنما</p>
          <h2>تنظیم فایل محلی وردپرس</h2>
        </div>

        <pre className="json-block">
{`DAMA_WORDPRESS_BASE_URL=http://damamedia.local
DAMA_WORDPRESS_USERNAME=tarkhani
DAMA_WORDPRESS_APP_PASSWORD=Application-Password-WordPress`}
        </pre>

        <p className="muted-note">
          پسورد باید Application Password وردپرس باشد، نه پسورد معمولی ورود به پنل.
        </p>
      </section>
    </main>
  );
}
