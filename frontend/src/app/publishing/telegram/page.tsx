import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { TelegramConnectionTestAction } from "../../../components/telegram-connection-test-action";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type TelegramConfig = {
  ready: boolean;
  missing: string[];
  bot_token_configured: boolean;
  default_chat_id_configured: boolean;
  default_chat_id_preview: string;
  secrets_redacted: boolean;
  message: string;
};

async function loadConfig(): Promise<TelegramConfig> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/telegram/config`, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return (await response.json()) as TelegramConfig;
  } catch {
    return {
      ready: false,
      missing: ["backend unreachable"],
      bot_token_configured: false,
      default_chat_id_configured: false,
      default_chat_id_preview: "",
      secrets_redacted: true,
      message: "Telegram config could not be loaded."
    };
  }
}

export default async function TelegramPublishingPage() {
  const config = await loadConfig();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تلگرام"
        title="وضعیت اتصال تلگرام"
        lead="اینجا وضعیت Bot Token و امکان ارسال تست تلگرام را بررسی می‌کنی. انتشار عمومی هنوز فعال نیست."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="آماده اتصال واقعی" value={config.ready ? "بله" : "نه"} helper="وضعیت env تلگرام" />
        <StatCard label="Bot Token" value={config.bot_token_configured ? "تنظیم شده" : "نیست"} helper="secret مخفی است" />
        <StatCard label="Default Chat ID" value={config.default_chat_id_configured ? "تنظیم شده" : "نیست"} helper={config.default_chat_id_preview || "اختیاری"} />
        <StatCard label="Secrets" value={config.secrets_redacted ? "مخفی" : "نامشخص"} helper="توکن در UI نمایش داده نمی‌شود" />
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
              <strong>Missing</strong>
              <span>{config.missing.length ? config.missing.join(", ") : ""}</span>
            </div>
            <div>
              <strong>Default Chat</strong>
              <span>{config.default_chat_id_preview || ""}</span>
            </div>
          </div>
        </section>

        <TelegramConnectionTestAction apiBaseUrl={API_BASE_URL} />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">راهنما</p>
          <h2>برای اتصال واقعی چه لازم است؟</h2>
        </div>

        <ol className="simple-steps">
          <li>در تلگرام با BotFather یک Bot بساز.</li>
          <li>Bot Token را داخل backend/.env.local بگذار.</li>
          <li>برای ارسال به کانال، Bot را admin کانال کن.</li>
          <li>شناسه کانال را به شکل @channel_username یا chat_id وارد کن.</li>
          <li>اول Dry-run بزن؛ بعد تست واقعی.</li>
        </ol>

        <pre className="json-block">
{`DAMA_TELEGRAM_BOT_TOKEN=123456:your-bot-token
DAMA_TELEGRAM_DEFAULT_CHAT_ID=@your_test_channel`}
        </pre>
      </section>
    </main>
  );
}
