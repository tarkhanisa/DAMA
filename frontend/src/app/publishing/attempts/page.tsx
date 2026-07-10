import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingAttempt = {
  id: string;
  variant_id: string;
  channel_name: string;
  channel_type: string;
  connector: string;
  mode: string;
  status: string;
  created_at: string;
  error?: string;
  response?: Record<string, unknown>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeAttempts(payload: unknown): PublishingAttempt[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : Array.isArray(record.items)
      ? record.items
      : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        variant_id: String(value.variant_id ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? ""),
        connector: String(value.connector ?? ""),
        mode: String(value.mode ?? ""),
        status: String(value.status ?? ""),
        created_at: String(value.created_at ?? ""),
        error: typeof value.error === "string" ? value.error : "",
        response: asRecord(value.response)
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

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    dry_run: "Dry-run",
    draft_created: "Draft ساخته شد",
    failed: "خطا",
    blocked: "مسدود شده",
    created: "ساخته شده"
  };

  return labels[status] ?? status;
}

export default async function PublishingAttemptsPage() {
  const attempts = await loadAttempts();
  const draftCount = attempts.filter((item) => item.status === "draft_created").length;
  const dryRunCount = attempts.filter((item) => item.status === "dry_run").length;
  const failedCount = attempts.filter((item) => item.status === "failed").length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="گزارش انتشار"
        title="تلاش‌های انتشار"
        lead="اینجا تلاش‌های ساخت پیش‌نویس، dry-run و خطاهای اتصال ثبت می‌شوند."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing">کانال‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه تلاش‌ها" value={attempts.length} helper="همه connector attempts" />
        <StatCard label="Draft ساخته‌شده" value={draftCount} helper="اتصال واقعی موفق" />
        <StatCard label="Dry-run" value={dryRunCount} helper="تست امن بدون انتشار" />
        <StatCard label="خطا" value={failedCount} helper="نیازمند بررسی" />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست</p>
          <h2>آخرین تلاش‌ها</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>وضعیت</th>
                <th>کانال</th>
                <th>Connector</th>
                <th>Mode</th>
                <th>زمان</th>
                <th>پیام</th>
              </tr>
            </thead>
            <tbody>
              {attempts.length > 0 ? (
                attempts.slice(0, 50).map((attempt) => (
                  <tr key={attempt.id}>
                    <td>
                      <span className={`status-badge status-${attempt.status}`}>
                        {statusLabel(attempt.status)}
                      </span>
                    </td>
                    <td>{attempt.channel_name || ""}</td>
                    <td>{attempt.connector}</td>
                    <td>{attempt.mode}</td>
                    <td>{attempt.created_at}</td>
                    <td>{attempt.error || String(attempt.response?.wordpress_link ?? "")}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>هنوز تلاش انتشاری ثبت نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
