import { CreatePublishingQueueItemForm } from "../../../components/create-publishing-queue-item-form";
import { PageHeader } from "../../../components/page-header";
import { RunPublishingQueueItemAction } from "../../../components/run-publishing-queue-item-action";
import { StatCard } from "../../../components/stat-card";
import {
  labelAttemptStatus,
  labelConnector,
  labelMode,
  labelQueueStatus
} from "../../../lib/persian-copy";

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

export default async function PublishingQueuePage() {
  const [queue, variants] = await Promise.all([loadQueue(), loadVariants()]);

  const queuedCount = queue.filter((item) => item.status === "queued").length;
  const doneCount = queue.filter((item) => item.status === "sent" || item.status === "dry_run_completed").length;
  const failedCount = queue.filter((item) => item.status === "failed" || item.status === "blocked").length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="صف انتشار"
        title="صف انتشار کنترل‌شده"
        lead="نسخه‌های آماده را اینجا وارد صف کن. اجرای واقعی همیشه دستی است و پیشنهاد می‌شود اول اجرای آزمایشی انجام شود."
      >
        <div className="actions">
          <a href="/publishing/variants">نسخه‌ها</a>
          <a href="/publishing/attempts">گزارش‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه آیتم‌ها" value={queue.length} helper="کل صف فعلی" />
        <StatCard label="در صف" value={queuedCount} helper="منتظر اجرا" />
        <StatCard label="انجام‌شده" value={doneCount} helper="موفق یا آزمایشی" />
        <StatCard label="نیازمند بررسی" value={failedCount} helper="خطا یا مسدود شده" />
      </section>

      <section className="dashboard-flow compact-flow" aria-label="مسیر صف انتشار">
        <div className="flow-card">
          <span className="flow-number">۱</span>
          <strong>نسخه آماده</strong>
          <p>متن کانالی تأیید شده باشد.</p>
        </div>

        <span className="flow-arrow">←</span>

        <div className="flow-card">
          <span className="flow-number">۲</span>
          <strong>افزودن به صف</strong>
          <p>مقصد و نوع اجرا را انتخاب کن.</p>
        </div>

        <span className="flow-arrow">←</span>

        <div className="flow-card">
          <span className="flow-number">۳</span>
          <strong>اجرای دستی</strong>
          <p>اول آزمایشی، بعد واقعی.</p>
        </div>
      </section>

      <section className="two-column">
        <CreatePublishingQueueItemForm apiBaseUrl={API_BASE_URL} variants={variants} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنمای ساده</p>
            <h2>چطور اشتباه نکنم؟</h2>
          </div>

          <ol className="simple-steps">
            <li>برای تست، نوع اجرا را «اجرای آزمایشی امن» بگذار.</li>
            <li>برای وردپرس واقعی، فقط پیش‌نویس ساخته می‌شود.</li>
            <li>برای تلگرام واقعی، فعلاً فقط پیام تست ارسال می‌شود.</li>
            <li>هر اجرا در گزارش‌ها ثبت می‌شود.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">آیتم‌های صف</p>
          <h2>آخرین کارهای آماده اجرا</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>وضعیت</th>
                <th>نسخه</th>
                <th>کانال</th>
                <th>مقصد</th>
                <th>نوع اجرا</th>
                <th>آخرین نتیجه</th>
                <th>عملیات</th>
              </tr>
            </thead>
            <tbody>
              {queue.length > 0 ? (
                queue.slice(0, 50).map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span className={`status-badge status-${item.status}`}>
                        {labelQueueStatus(item.status)}
                      </span>
                    </td>
                    <td>{item.variant_title || "بدون عنوان"}</td>
                    <td>{item.channel_name || labelConnector(item.channel_type)}</td>
                    <td>{labelConnector(item.connector)}</td>
                    <td>{labelMode(item.mode)}</td>
                    <td>
                      {item.latest_attempt_id ? (
                        <a href={`/publishing/attempts/${item.latest_attempt_id}`}>
                          {labelAttemptStatus(item.latest_attempt_status)}
                        </a>
                      ) : (
                        "—"
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
                  <td colSpan={7}>فعلاً چیزی در صف انتشار نیست.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
