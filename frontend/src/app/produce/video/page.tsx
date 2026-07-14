import { CreateLocalVideoJobForm } from "../../../components/create-local-video-job-form";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { formatPersianDate } from "../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type LocalVideoJob = {
  id: string;
  project_name: string;
  title: string;
  status: string;
  duration_seconds: number;
  aspect_ratio: string;
  created_at: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getItems(payload: unknown): Record<string, unknown>[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return source.map(asRecord);
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

function normalizeJobs(payload: unknown): LocalVideoJob[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      project_name: String(item.project_name ?? ""),
      title: String(item.title ?? ""),
      status: String(item.status ?? ""),
      duration_seconds: Number(item.duration_seconds ?? 0),
      aspect_ratio: String(item.aspect_ratio ?? ""),
      created_at: String(item.created_at ?? "")
    }))
    .filter((item) => item.id);
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

export default async function LocalVideoPage() {
  const [configPayload, jobsPayload] = await Promise.all([
    loadJson("/publishing/local-video/config"),
    loadJson("/publishing/local-video/jobs")
  ]);

  const config = asRecord(configPayload);
  const jobs = normalizeJobs(jobsPayload);
  const ready = Boolean(config.ready);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید ویدیو لوکال"
        title="ویدیو از تصویر و پرامپت"
        lead="تصویر شروع را بده، اگر لازم بود تصویر پایان را هم بده، پرامپت حرکت را بنویس و مدت/نسبت تصویر را تنظیم کن."
      >
        <div className="actions">
          <a href="/produce">بازگشت به تولید</a>
          <a href="/produce/video/setup">تنظیم ابزارهای لوکال</a>
          <a href="/other">سایر</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت موتور" value={ready ? "آماده" : "تنظیم نشده"} helper={String(config.message ?? "—")} />
        <StatCard label="مدت پیش‌فرض" value="۴ ثانیه" helper="قابل تغییر از فرم" />
        <StatCard label="نسبت تصویر" value="چندحالته" helper="16:9، 9:16، 1:1 و..." />
        <StatCard label="درخواست‌ها" value={jobs.length} helper="jobهای ثبت‌شده" />
      </section>

      <section className="two-column">
        <CreateLocalVideoJobForm apiBaseUrl={API_BASE_URL} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>این ابزار چه کار می‌کند؟</h2>
          </div>

          <ol className="simple-steps">
            <li>فعلاً درخواست ویدیو را استاندارد ثبت می‌کند.</li>
            <li>Dry-run فایل ورودی ابزار لوکال را می‌سازد.</li>
            <li>برای ساخت واقعی باید موتور لوکال را از طریق env وصل کنیم.</li>
            <li>بعداً می‌توانیم ComfyUI یا ابزار مشابه را به همین صفحه وصل کنیم.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">درخواست‌های اخیر</p>
          <h2>ویدیوهای ثبت‌شده</h2>
        </div>

        <div className="campaign-grid">
          {jobs.length > 0 ? (
            jobs.slice(0, 40).map((job) => (
              <a className="campaign-card" href={`/produce/video/${job.id}`} key={job.id}>
                <span className={`status-badge status-${job.status}`}>
                  {statusLabel(job.status)}
                </span>
                <strong>{job.title || "ویدیوی بدون عنوان"}</strong>
                <p>{job.project_name || "بدون پروژه"}</p>
                <dl>
                  <div>
                    <dt>مدت</dt>
                    <dd>{job.duration_seconds} ثانیه</dd>
                  </div>
                  <div>
                    <dt>نسبت</dt>
                    <dd>{job.aspect_ratio}</dd>
                  </div>
                  <div>
                    <dt>زمان</dt>
                    <dd>{formatPersianDate(job.created_at)}</dd>
                  </div>
                </dl>
              </a>
            ))
          ) : (
            <p className="muted-note">هنوز درخواست ویدیویی ثبت نشده است.</p>
          )}
        </div>
      </section>
    </main>
  );
}
