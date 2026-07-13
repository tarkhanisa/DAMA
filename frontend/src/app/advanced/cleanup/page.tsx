import { CleanupTestDataAction } from "../../../components/cleanup-test-data-action";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type FileSummary = {
  before?: number;
  after?: number;
  removed?: number;
};

type CleanupPreview = {
  ok?: boolean;
  totals?: {
    removed?: number;
  };
  files?: Record<string, FileSummary>;
};

async function loadPreview(): Promise<CleanupPreview> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/cleanup/test-data/preview`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return (await response.json()) as CleanupPreview;
  } catch {
    return {};
  }
}

export default async function AdvancedCleanupPage() {
  const preview = await loadPreview();
  const files = preview.files ?? {};
  const totalRemoved = preview.totals?.removed ?? 0;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="پیشرفته"
        title="پاک‌سازی داده‌های تستی"
        lead="این ابزار فقط آیتم‌های smoke/test را از داده‌های runtime پاک می‌کند و قبل از حذف backup می‌گیرد."
      >
        <div className="actions">
          <a href="/advanced">بازگشت به پیشرفته</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="قابل حذف" value={totalRemoved} helper="بر اساس preview فعلی" />
        <StatCard label="صف انتشار" value={files["publishing_queue.json"]?.removed ?? 0} helper="آیتم‌های تستی" />
        <StatCard label="نسخه‌ها" value={files["publishing_variants.json"]?.removed ?? 0} helper="variantهای تستی" />
        <StatCard label="گزارش‌ها" value={files["publishing_attempts.json"]?.removed ?? 0} helper="attemptهای تستی" />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">عملیات امن</p>
            <h2>پاک‌سازی با backup</h2>
          </div>

          <p className="muted-note">
            کانال‌های تمیز «وردپرس لوکال دامامدیا» و «تلگرام تست دامامدیا» حفظ می‌شوند.
            آیتم‌هایی که با smoke/test ساخته شده‌اند حذف می‌شوند.
          </p>

          <CleanupTestDataAction apiBaseUrl={API_BASE_URL} />
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>چه چیزی حذف می‌شود؟</h2>
          </div>

          <ol className="simple-steps">
            <li>کانال‌های smoke و تست موقت.</li>
            <li>نسخه‌هایی که برای smoke test ساخته شده‌اند.</li>
            <li>گزارش‌های اجرای آزمایشی تستی.</li>
            <li>آیتم‌های صف مربوط به تست‌ها.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش پیش‌نمایش فنی پاک‌سازی</summary>
          <pre className="json-block">{JSON.stringify(preview, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
