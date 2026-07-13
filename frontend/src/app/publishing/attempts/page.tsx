import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import {
  attemptResultSummary,
  formatPersianDate,
  friendlyErrorMessage,
  labelAttemptStatus,
  labelConnector,
  labelMode,
  shortId
} from "../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingAttempt = {
  id: string;
  connector: string;
  mode: string;
  status: string;
  variant_id: string;
  channel_name: string;
  channel_type: string;
  created_at: string;
  updated_at: string;
  error: string;
  target_url: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeAttempts(payload: unknown): PublishingAttempt[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];

  return source
    .map((item) => {
      const value = asRecord(item);
      const request = asRecord(value.request);
      const response = asRecord(value.response);

      return {
        id: String(value.id ?? ""),
        connector: String(value.connector ?? value.channel_type ?? request.connector ?? ""),
        mode: String(value.mode ?? request.mode ?? ""),
        status: String(value.status ?? ""),
        variant_id: String(value.variant_id ?? request.variant_id ?? ""),
        channel_name: String(value.channel_name ?? request.channel_name ?? response.channel_name ?? ""),
        channel_type: String(value.channel_type ?? request.channel_type ?? ""),
        created_at: String(value.created_at ?? value.createdAt ?? ""),
        updated_at: String(value.updated_at ?? value.updatedAt ?? ""),
        error: String(value.error ?? response.error ?? ""),
        target_url: String(value.target_url ?? request.target_url ?? response.target_url ?? "")
      };
    })
    .filter((item) => item.id);
}

async function loadAttempts(): Promise<PublishingAttempt[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/attempts`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeAttempts(await response.json());
  } catch {
    return [];
  }
}

export default async function PublishingAttemptsPage() {
  const attempts = await loadAttempts();

  const successfulCount = attempts.filter((item) =>
    ["draft_created", "test_sent", "dry_run"].includes(item.status)
  ).length;

  const failedCount = attempts.filter((item) =>
    ["failed", "blocked"].includes(item.status)
  ).length;

  const latestAttempt = attempts[0];

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="گزارش‌ها"
        title="گزارش اجرای انتشار"
        lead="هر بار که وردپرس، تلگرام یا اجرای آزمایشی را اجرا می‌کنی، نتیجه اینجا ثبت می‌شود."
      >
        <div className="actions">
          <a href="/publishing/queue">صف انتشار</a>
          <a href="/publishing">مرکز انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کل گزارش‌ها" value={attempts.length} helper="همه اجراهای ثبت‌شده" />
        <StatCard label="موفق / آزمایشی" value={successfulCount} helper="بدون خطای جدی" />
        <StatCard label="نیازمند بررسی" value={failedCount} helper="خطا یا توقف ایمنی" />
        <StatCard
          label="آخرین نتیجه"
          value={latestAttempt ? labelAttemptStatus(latestAttempt.status) : ""}
          helper={latestAttempt ? attemptResultSummary(latestAttempt.status) : "هنوز گزارشی ثبت نشده"}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست گزارش‌ها</p>
          <h2>آخرین اجراها</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>نتیجه</th>
                <th>مقصد</th>
                <th>نوع اجرا</th>
                <th>زمان</th>
                <th>خطا</th>
                <th>جزئیات</th>
              </tr>
            </thead>
            <tbody>
              {attempts.length > 0 ? (
                attempts.slice(0, 80).map((attempt) => (
                  <tr key={attempt.id}>
                    <td>
                      <span className={`status-badge status-${attempt.status}`}>
                        {labelAttemptStatus(attempt.status)}
                      </span>
                    </td>
                    <td>{labelConnector(attempt.connector || attempt.channel_type)}</td>
                    <td>{labelMode(attempt.mode || attempt.connector)}</td>
                    <td>{formatPersianDate(attempt.created_at)}</td>
                    <td>{attempt.error ? friendlyErrorMessage(attempt.error) : ""}</td>
                    <td>
                      <a href={`/publishing/attempts/${attempt.id}`}>
                        مشاهده جزئیات {shortId(attempt.id)}
                      </a>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>فعلاً گزارشی ثبت نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
