import { PageHeader } from "../components/page-header";
import { StatCard } from "../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type DashboardStats = {
  projects: number;
  contentAssets: number;
  backendStatus: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadStats(): Promise<DashboardStats> {
  try {
    const [dashboardResponse, projectsResponse, assetsResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/dashboard/summary`, { cache: "no-store" }),
      fetch(`${API_BASE_URL}/projects`, { cache: "no-store" }),
      fetch(`${API_BASE_URL}/content-assets`, { cache: "no-store" })
    ]);

    const dashboard = dashboardResponse.ok ? asRecord(await dashboardResponse.json()) : {};
    const projectsPayload = projectsResponse.ok ? await projectsResponse.json() : [];
    const assetsPayload = assetsResponse.ok ? await assetsResponse.json() : [];

    const projectsRecord = asRecord(projectsPayload);
    const assetsRecord = asRecord(assetsPayload);

    const projectItems = Array.isArray(projectsPayload)
      ? projectsPayload
      : Array.isArray(projectsRecord.items)
        ? projectsRecord.items
        : Array.isArray(projectsRecord.projects)
          ? projectsRecord.projects
          : [];

    const assetItems = Array.isArray(assetsPayload)
      ? assetsPayload
      : Array.isArray(assetsRecord.items)
        ? assetsRecord.items
        : Array.isArray(assetsRecord.assets)
          ? assetsRecord.assets
          : [];

    return {
      projects: Number(dashboard.projects_count ?? dashboard.project_count ?? projectItems.length),
      contentAssets: Number(
        dashboard.content_assets_count ?? dashboard.asset_count ?? assetItems.length
      ),
      backendStatus: "وصل است"
    };
  } catch {
    return {
      projects: 0,
      contentAssets: 0,
      backendStatus: "نیاز به بررسی"
    };
  }
}

export default async function DashboardPage() {
  const stats = await loadStats();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="داشبورد دامامدیا"
        title="از اینجا شروع کن"
        lead="این پنل برای مدیریت پروژه‌ها، تولید محتوای باکیفیت، ذخیره خروجی‌ها و بررسی سلامت سیستم ساخته شده است."
      >
        <div className="actions">
          <a href="/projects/new">ساخت پروژه جدید</a>
          <a href="/generate">تولید محتوا</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="پروژه‌ها" value={stats.projects} helper="پرونده‌های کاری داخل سیستم" />
        <StatCard label="محتواها" value={stats.contentAssets} helper="خروجی‌ها و دارایی‌های ذخیره‌شده" />
        <StatCard label="وضعیت بک‌اند" value={stats.backendStatus} helper="ارتباط پنل با FastAPI" />
        <StatCard label="حالت استفاده" value="محلی" helper="نسخه توسعه روی کامپیوتر شما" />
      </section>

      <section className="simple-start-grid">
        <a className="simple-start-card" href="/projects/new">
          <span></span>
          <strong>اول پروژه بساز</strong>
          <p>مثلاً گرگران، اورماشاپ یا دامامدیا. هر تولید محتوا بهتر است داخل یک پروژه واقعی ذخیره شود.</p>
        </a>

        <a className="simple-start-card" href="/generate">
          <span></span>
          <strong>بعد محتوا تولید کن</strong>
          <p>پروژه را انتخاب کن، brief بده، سطح کیفیت را تعیین کن و خروجی را ذخیره کن.</p>
        </a>

        <a className="simple-start-card" href="/content-assets">
          <span></span>
          <strong>خروجی‌ها را ببین</strong>
          <p>محتواهای تولیدشده اینجا ذخیره می‌شوند و بعداً قابل ویرایش، خروجی‌گرفتن و استفاده هستند.</p>
        </a>

        <a className="simple-start-card" href="/runtime">
          <span></span>
          <strong>سلامت سیستم را چک کن</strong>
          <p>اگر تولید محتوا درست کار نکرد، اول وضعیت بک‌اند و Ollama را در این بخش ببین.</p>
        </a>
      </section>

      <section className="panel simple-help-panel">
        <div className="panel-heading">
          <p className="eyebrow">راهنمای سریع</p>
          <h2>برای تست اول چه کار کنم؟</h2>
        </div>

        <ol className="simple-steps">
          <li>روی «ساخت پروژه جدید» بزن.</li>
          <li>یک پروژه واقعی مثل «محتوای سایت گرگران» بساز.</li>
          <li>از منوی بالا وارد «تولید محتوا» شو.</li>
          <li>پروژه، نوع محتوا، مخاطب و لحن را انتخاب کن.</li>
          <li>brief را بنویس و دکمه «تولید محتوا» را بزن.</li>
        </ol>
      </section>
    </main>
  );
}
