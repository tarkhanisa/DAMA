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
