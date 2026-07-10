import { ErrorPanel } from "../../../../components/error-panel";
import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type AttemptDetailPageProps = {
  params: Promise<{
    attemptId: string;
  }>;
};

type PublishingAttempt = {
  id: string;
  variant_id: string;
  content_asset_id?: string;
  channel_id?: string;
  channel_name?: string;
  channel_type?: string;
  connector?: string;
  mode?: string;
  requested_by?: string;
  notes?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  target_url?: string;
  request_preview?: Record<string, unknown>;
  response?: Record<string, unknown>;
  error?: string;
  error_detail?: Record<string, unknown>;
  validation?: Record<string, unknown>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadAttempt(attemptId: string): Promise<PublishingAttempt | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/attempts/${attemptId}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as PublishingAttempt;
  } catch {
    return null;
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

export default async function PublishingAttemptDetailPage({
  params
}: AttemptDetailPageProps) {
  const { attemptId } = await params;
  const attempt = await loadAttempt(attemptId);

  if (!attempt) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="گزارش انتشار"
          title="تلاش انتشار پیدا نشد"
          message="این گزارش در بک‌اند پیدا نشد."
        />
      </main>
    );
  }

  const response = asRecord(attempt.response);
  const requestPreview = asRecord(attempt.request_preview);
  const validation = asRecord(attempt.validation);
  const errorDetail = asRecord(attempt.error_detail);

  const wordpressLink = String(response.wordpress_link ?? "");
  const wordpressPostId = String(response.wordpress_post_id ?? "");

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="جزئیات تلاش انتشار"
        title={`${attempt.connector ?? "connector"}  ${statusLabel(attempt.status)}`}
        lead="این صفحه گزارش دقیق یک تلاش انتشار یا ساخت Draft را نشان می‌دهد."
      >
        <div className="actions">
          <a href="/publishing/attempts">بازگشت به گزارش‌ها</a>
          <a href={`/publishing/variants/${attempt.variant_id}`}>بازگشت به نسخه</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(attempt.status)} helper={attempt.mode ?? ""} />
        <StatCard label="کانال" value={attempt.channel_name ?? ""} helper={attempt.channel_type ?? ""} />
        <StatCard label="درخواست‌کننده" value={attempt.requested_by ?? ""} helper={attempt.created_at ?? ""} />
        <StatCard label="WordPress Post" value={wordpressPostId || ""} helper="شناسه Draft در وردپرس" />
      </section>

      {wordpressLink ? (
        <section className="panel success-panel">
          <div className="panel-heading">
            <p className="eyebrow">Draft ساخته شد</p>
            <h2>لینک وردپرس</h2>
          </div>

          <p>
            پیش‌نویس وردپرس ساخته شده است. برای مشاهده یا ادامه ویرایش، لینک زیر را باز کن:
          </p>

          <a className="primary-link" href={wordpressLink} target="_blank" rel="noreferrer">
            باز کردن Draft وردپرس
          </a>
        </section>
      ) : null}

      {attempt.error ? (
        <section className="panel danger-panel">
          <div className="panel-heading">
            <p className="eyebrow">خطا</p>
            <h2>پیام خطا</h2>
          </div>

          <p>{attempt.error}</p>

          {Object.keys(errorDetail).length ? (
            <pre className="json-block">{JSON.stringify(errorDetail, null, 2)}</pre>
          ) : null}
        </section>
      ) : null}

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Request Preview</p>
            <h2>چیزی که قرار بود ساخته شود</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>Title</strong>
              <span>{String(requestPreview.title ?? "")}</span>
            </div>
            <div>
              <strong>Slug</strong>
              <span>{String(requestPreview.slug ?? "")}</span>
            </div>
            <div>
              <strong>Excerpt</strong>
              <span>{String(requestPreview.excerpt ?? "")}</span>
            </div>
            <div>
              <strong>SEO Title</strong>
              <span>{String(requestPreview.seo_title ?? "")}</span>
            </div>
            <div>
              <strong>Meta Description</strong>
              <span>{String(requestPreview.meta_description ?? "")}</span>
            </div>
          </div>

          <pre className="json-block">{JSON.stringify(requestPreview, null, 2)}</pre>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Validation</p>
            <h2>نتیجه اعتبارسنجی</h2>
          </div>

          <pre className="json-block">{JSON.stringify(validation, null, 2)}</pre>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Response</p>
          <h2>پاسخ Connector</h2>
        </div>

        <pre className="json-block">{JSON.stringify(response, null, 2)}</pre>
      </section>
    </main>
  );
}
