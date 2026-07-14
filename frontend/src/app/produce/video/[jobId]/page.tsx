import { PageHeader } from "../../../../components/page-header";
import { RunLocalVideoJobAction } from "../../../../components/run-local-video-job-action";
import { StatCard } from "../../../../components/stat-card";
import { formatPersianDate, shortId } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type Props = {
  params: Promise<{
    jobId: string;
  }>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadJob(jobId: string): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/local-video/jobs/${jobId}`, {
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

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "ثبت‌شده",
    dry_run: "Dry-run انجام شد",
    blocked: "نیازمند تنظیم",
    running: "در حال اجرا",
    completed: "ساخته شد",
    failed: "خطا"
  };

  return labels[status] ?? "نامشخص";
}

export default async function LocalVideoJobPage({ params }: Props) {
  const { jobId } = await params;
  const job = await loadJob(jobId);

  const status = String(job.status ?? "");
  const outputPath = String(job.output_path ?? "");
  const error = String(job.error ?? "");

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="درخواست ویدیو"
        title={String(job.title ?? "ویدیوی لوکال")}
        lead={String(job.prompt ?? "درخواست تولید ویدیو از تصویر و پرامپت.")}
      >
        <div className="actions">
          <a href="/produce/video">بازگشت به ویدیوها</a>
          <a href="/produce">تولید</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(status)} helper={`شناسه: ${shortId(jobId)}`} />
        <StatCard label="مدت" value={`${String(job.duration_seconds ?? "۴")} ثانیه`} helper="قابل تنظیم در فرم" />
        <StatCard label="نسبت تصویر" value={String(job.aspect_ratio ?? "16:9")} helper={`FPS: ${String(job.fps ?? "24")}`} />
        <StatCard label="زمان ساخت" value={formatPersianDate(String(job.created_at ?? ""))} helper={String(job.project_name ?? "—")} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">پرامپت</p>
            <h2>حرکت و حس ویدیو</h2>
          </div>

          <div className="generated-output">
            <p>{String(job.prompt ?? "بدون پرامپت")}</p>
          </div>

          <dl className="detail-list">
            <div>
              <dt>تصویر شروع</dt>
              <dd>{String(job.start_image ?? "—")}</dd>
            </div>
            <div>
              <dt>تصویر پایان</dt>
              <dd>{String(job.end_image ?? "—") || "—"}</dd>
            </div>
            <div>
              <dt>خروجی</dt>
              <dd>{outputPath || "هنوز ساخته نشده"}</dd>
            </div>
            <div>
              <dt>خطا</dt>
              <dd>{error || "—"}</dd>
            </div>
          </dl>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">اجرا</p>
            <h2>Dry-run یا موتور لوکال</h2>
          </div>

          <p className="muted-note">
            Dry-run امن است و فقط فایل ورودی را آماده می‌کند. اجرای موتور لوکال وقتی کار می‌کند که
            DAMA_LOCAL_VIDEO_COMMAND تنظیم شده باشد.
          </p>

          <RunLocalVideoJobAction apiBaseUrl={API_BASE_URL} jobId={jobId} />
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی</summary>
          <pre className="json-block">{JSON.stringify(job, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
