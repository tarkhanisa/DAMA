import { CreatePublishingQueueItemForm } from "../../../components/create-publishing-queue-item-form";
import { PageHeader } from "../../../components/page-header";
import { RunPublishingQueueItemAction } from "../../../components/run-publishing-queue-item-action";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingQueueItem = {
  id: string;
  variant_id: string;
  variant_title: string;
  channel_name: string;
  channel_type: string;
  connector: string;
  mode: string;
  status: string;
  created_at: string;
  latest_attempt_id?: string;
  latest_attempt_status?: string;
  error?: string;
};

type PublishingVariantOption = {
  id: string;
  variant_title: string;
  channel_name: string;
  channel_type: string;
  status: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeQueue(payload: unknown): PublishingQueueItem[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        variant_id: String(value.variant_id ?? ""),
        variant_title: String(value.variant_title ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? ""),
        connector: String(value.connector ?? ""),
        mode: String(value.mode ?? ""),
        status: String(value.status ?? ""),
        created_at: String(value.created_at ?? ""),
        latest_attempt_id: String(value.latest_attempt_id ?? ""),
        latest_attempt_status: String(value.latest_attempt_status ?? ""),
        error: String(value.error ?? "")
      };
    })
    .filter((item) => item.id);
}

function normalizeVariants(payload: unknown): PublishingVariantOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        variant_title: String(value.variant_title ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? ""),
        status: String(value.status ?? "")
      };
    })
    .filter((item) => item.id)
    .filter((item) => ["approved", "ready_for_publish", "scheduled"].includes(item.status))
    .filter((item) => ["wordpress", "telegram"].includes(item.channel_type));
}

async function loadQueue(): Promise<PublishingQueueItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/queue`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeQueue(await response.json());
  } catch {
    return [];
  }
}

async function loadVariants(): Promise<PublishingVariantOption[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/variants`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeVariants(await response.json());
  } catch {
    return [];
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    queued: "در صف",
    running: "در حال اجرا",
    dry_run_completed: "Dry-run انجام شد",
    sent: "ارسال/ساخت انجام شد",
    failed: "خطا",
    blocked: "مسدود",
    cancelled: "لغو شده"
  };

  return labels[status] ?? status;
}

export default async function PublishingQueuePage() {
  const [queue, variants] = await Promise.all([loadQueue(), loadVariants()]);

  const queuedCount = queue.filter((item) => item.status === "queued").length;
  const sentCount = queue.filter((item) => item.status === "sent").length;
  const failedCount = queue.filter((item) => item.status === "failed" || item.status === "blocked").length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="صف انتشار"
        title="Publishing Queue"
        lead="اینجا نسخه‌های آماده انتشار را به صف اضافه می‌کنی و اجرای connectorها را دستی انجام می‌دهی."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه آیتم‌ها" value={queue.length} helper="همه صف" />
        <StatCard label="در صف" value={queuedCount} helper="منتظر اجرا" />
        <StatCard label="انجام‌شده" value={sentCount} helper="Draft یا Test Sent" />
        <StatCard label="خطادار" value={failedCount} helper="نیازمند بررسی" />
      </section>

      <section className="two-column">
        <CreatePublishingQueueItemForm apiBaseUrl={API_BASE_URL} variants={variants} />

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>روش امن استفاده</h2>
          </div>

          <ol className="simple-steps">
            <li>اول variant را در صفحه بازبینی روی آماده انتشار بگذار.</li>
            <li>بعد آن را به صف اضافه کن.</li>
            <li>اول Mode را Dry-run بگذار.</li>
            <li>اگر dry-run درست بود، بعداً mode واقعی را انتخاب کن.</li>
            <li>هر اجرا یک publishing attempt ثبت می‌کند.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست صف</p>
          <h2>آخرین آیتم‌ها</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>وضعیت</th>
                <th>عنوان</th>
                <th>کانال</th>
                <th>Connector</th>
                <th>Mode</th>
                <th>آخرین Attempt</th>
                <th>اجرا</th>
              </tr>
            </thead>
            <tbody>
              {queue.length > 0 ? (
                queue.slice(0, 50).map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span className={`status-badge status-${item.status}`}>
                        {statusLabel(item.status)}
                      </span>
                    </td>
                    <td>{item.variant_title || ""}</td>
                    <td>{item.channel_name || item.channel_type || ""}</td>
                    <td>{item.connector}</td>
                    <td>{item.mode}</td>
                    <td>
                      {item.latest_attempt_id ? (
                        <a href={`/publishing/attempts/${item.latest_attempt_id}`}>
                          {item.latest_attempt_status || "attempt"}
                        </a>
                      ) : (
                        ""
                      )}
                    </td>
                    <td>
                      <RunPublishingQueueItemAction
                        apiBaseUrl={API_BASE_URL}
                        queueId={item.id}
                        status={item.status}
                      />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>هنوز آیتمی در صف انتشار ثبت نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
