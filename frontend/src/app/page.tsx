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
