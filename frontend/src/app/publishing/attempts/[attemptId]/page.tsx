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
