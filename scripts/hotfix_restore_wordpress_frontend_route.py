from pathlib import Path

ROOT = Path("I:/DAMA")

def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")

write_file(
    "frontend/src/components/wordpress-connection-test-action.tsx",
    r'''
"use client";

import { useState } from "react";

type WordPressConnectionTestActionProps = {
  apiBaseUrl: string;
};

export function WordPressConnectionTestAction({
  apiBaseUrl
}: WordPressConnectionTestActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  async function handleTest() {
    setIsTesting(true);
    setMessage("");
    setRaw(null);

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/wordpress/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ mode })
      });

      const payload = await response.json();
      setRaw(payload);
      setMessage(payload.message ?? `HTTP ${response.status}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">تست اتصال</p>
        <h2>اتصال وردپرس را بررسی کن</h2>
      </div>

      <div className="enhance-variant-action">
        <label>
          حالت تست
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="wordpress">تست واقعی وردپرس</option>
          </select>
        </label>

        <button type="button" onClick={handleTest} disabled={isTesting}>
          {isTesting ? "در حال تست..." : "تست وردپرس"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}
      </div>

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}
    '''
)

write_file(
    "frontend/src/app/publishing/wordpress/page.tsx",
    r'''
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
    '''
)

print("WordPress frontend route restored.")
