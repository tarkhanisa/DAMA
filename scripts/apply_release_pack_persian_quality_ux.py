from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/projects", label: "پروژه‌ها" },
  { href: "/content-assets", label: "محتواها" },
  { href: "/generate", label: "تولید محتوا" },
  { href: "/workflows", label: "جریان کار" },
  { href: "/search", label: "جستجو" },
  { href: "/runtime", label: "سلامت سیستم" },
  { href: "/operations", label: "عملیات" },
  { href: "/exports", label: "خروجی‌ها" },
  { href: "/maintenance", label: "نگهداری" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="ناوبری دامامدیا">
      {navItems.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "active" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
    ''',
)


write_file(
    "frontend/src/app/page.tsx",
    r'''
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
    ''',
)


write_file(
    "frontend/src/app/projects/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ProjectItem = {
  id: string;
  name: string;
  project_type: string;
  language: string;
  status: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeProjects(payload: unknown): ProjectItem[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : Array.isArray(record.items)
      ? record.items
      : Array.isArray(record.projects)
        ? record.projects
        : Array.isArray(record.data)
          ? record.data
          : [];

  return source
    .map((item) => {
      const value = asRecord(item);
      const id = String(value.id ?? "");
      const name = String(value.name ?? value.title ?? id);

      return {
        id,
        name,
        project_type: String(value.project_type ?? value.type ?? "content_campaign"),
        language: String(value.language ?? "fa"),
        status: String(value.status ?? "draft")
      };
    })
    .filter((project) => project.id && project.name);
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: "فعال",
    draft: "پیش‌نویس",
    review: "در بازبینی",
    archived: "آرشیو"
  };

  return labels[status] ?? status;
}

async function loadProjects(): Promise<ProjectItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/projects`, { cache: "no-store" });

    if (!response.ok) {
      return [];
    }

    return normalizeProjects(await response.json());
  } catch {
    return [];
  }
}

export default async function ProjectsPage() {
  const projects = await loadProjects();
  const activeCount = projects.filter((project) => project.status === "active").length;
  const draftCount = projects.filter((project) => project.status === "draft").length;
  const realLookingProjects = projects.filter(
    (project) => !project.name.toLowerCase().startsWith("dama ")
  );

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="پروژه‌ها"
        title="پرونده‌های کاری"
        lead="هر کار واقعی را داخل یک پروژه جدا نگه دار؛ مثلاً گرگران، اورماشاپ، دامامدیا یا یک کمپین محتوایی."
      >
        <div className="actions">
          <a href="/projects/new">ساخت پروژه جدید</a>
          <a href="/generate">تولید محتوا</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه پروژه‌ها" value={projects.length} helper="شامل پروژه‌های تستی و واقعی" />
        <StatCard label="پروژه‌های واقعی‌تر" value={realLookingProjects.length} helper="غیر از پروژه‌های تستی DAMA" />
        <StatCard label="فعال" value={activeCount} helper="پروژه‌های آماده کار" />
        <StatCard label="پیش‌نویس" value={draftCount} helper="پروژه‌های هنوز تکمیل‌نشده" />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست پروژه‌ها</p>
          <h2>روی پروژه واقعی کلیک کن</h2>
        </div>

        <p className="muted-note">
          پروژه‌هایی که با «DAMA ...» شروع می‌شوند معمولاً برای تست‌های فنی ساخته شده‌اند. برای کار جدی بهتر است یک پروژه واقعی تازه بسازی.
        </p>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>نام پروژه</th>
                <th>نوع</th>
                <th>زبان</th>
                <th>وضعیت</th>
                <th>اقدام</th>
              </tr>
            </thead>
            <tbody>
              {projects.length > 0 ? (
                projects.map((project) => (
                  <tr key={project.id}>
                    <td>
                      <a className="table-link" href={`/projects/${project.id}`}>
                        {project.name}
                      </a>
                    </td>
                    <td>{project.project_type}</td>
                    <td>{project.language}</td>
                    <td>
                      <span className={`status-badge status-${project.status}`}>
                        {statusLabel(project.status)}
                      </span>
                    </td>
                    <td>
                      <a href={`/generate?project_id=${project.id}`}>تولید محتوا</a>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>هنوز پروژه‌ای پیدا نشد.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/generate/page.tsx",
    r'''
import { GenerateContentForm } from "../../components/generate-content-form";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

type ProjectOption = {
  id: string;
  name: string;
  status?: string;
  project_type?: string;
};

type ContentTypeOption = {
  key: string;
  label: string;
  description?: string;
};

type ModelOption = {
  name: string;
  provider?: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

async function getJson(endpoint: string): Promise<unknown> {
  const response = await fetch(endpoint, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

function normalizeProjects(payload: unknown): ProjectOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.items ?? record.projects ?? record.data);

  return source
    .map((item) => {
      const value = asRecord(item);
      const id = String(value.id ?? "");
      const name = String(value.name ?? value.title ?? id);

      return {
        id,
        name,
        status: typeof value.status === "string" ? value.status : undefined,
        project_type:
          typeof value.project_type === "string" ? value.project_type : undefined
      };
    })
    .filter((project) => project.id && project.name);
}

function normalizeContentTypes(payload: unknown): ContentTypeOption[] {
  const record = asRecord(payload);
  const directSource = Array.isArray(payload)
    ? payload
    : asArray(record.items ?? record.content_types ?? record.types ?? record.data);

  const source =
    directSource.length > 0
      ? directSource
      : Object.entries(record).map(([key, value]) => ({
          key,
          ...(typeof value === "object" && value !== null ? value : {})
        }));

  return source
    .map((item) => {
      if (typeof item === "string") {
        return {
          key: item,
          label: item
        };
      }

      const value = asRecord(item);
      const key = String(value.key ?? value.id ?? value.name ?? "");
      const rawLabel = String(value.label ?? value.name ?? value.title ?? key);

      const labelMap: Record<string, string> = {
        general: "عمومی",
        article: "مقاله",
        summary: "خلاصه",
        pitch: "پیچ / معرفی سرمایه‌گذاری",
        blog_post: "پست وبلاگ",
        product_description: "توضیح محصول",
        social_post: "پست شبکه اجتماعی"
      };

      return {
        key,
        label: labelMap[key] ?? rawLabel,
        description:
          typeof value.description === "string" ? value.description : undefined
      };
    })
    .filter((type) => type.key && type.label);
}

function normalizeModels(payload: unknown): ModelOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.models ?? record.items ?? record.data);

  return source
    .map((item) => {
      if (typeof item === "string") {
        return {
          name: item,
          provider: "ollama"
        };
      }

      const value = asRecord(item);
      const name = String(value.name ?? value.model ?? value.id ?? "");

      return {
        name,
        provider: typeof value.provider === "string" ? value.provider : "ollama"
      };
    })
    .filter((model) => model.name);
}

async function loadProjects(): Promise<ProjectOption[]> {
  try {
    const payload = await getJson(`${API_BASE_URL}/projects`);
    return normalizeProjects(payload);
  } catch {
    return [];
  }
}

async function loadContentTypes(): Promise<ContentTypeOption[]> {
  try {
    const payload = await getJson(`${API_BASE_URL}/content/types`);
    const normalized = normalizeContentTypes(payload);

    return normalized.length > 0
      ? normalized
      : [
          { key: "general", label: "عمومی" },
          { key: "article", label: "مقاله" },
          { key: "summary", label: "خلاصه" },
          { key: "pitch", label: "پیچ / معرفی سرمایه‌گذاری" }
        ];
  } catch {
    return [
      { key: "general", label: "عمومی" },
      { key: "article", label: "مقاله" },
      { key: "summary", label: "خلاصه" },
      { key: "pitch", label: "پیچ / معرفی سرمایه‌گذاری" }
    ];
  }
}

async function loadModels(): Promise<ModelOption[]> {
  try {
    const payload = await getJson(`${API_BASE_URL}/models`);
    return normalizeModels(payload);
  } catch {
    return [];
  }
}

export default async function GeneratePage() {
  const [projects, contentTypes, models] = await Promise.all([
    loadProjects(),
    loadContentTypes(),
    loadModels()
  ]);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید محتوا"
        title="تولید محتوای باکیفیت"
        lead="اینجا فقط یک خروجی در هر بار تولید می‌شود تا کنترل کیفیت حفظ شود. برای نتیجه بهتر، هدف، مخاطب، لحن و قالب خروجی را دقیق انتخاب کن."
      >
        <div className="actions">
          <a href="/projects/new">ساخت پروژه</a>
          <a href="/content-assets">محتواهای ذخیره‌شده</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="پروژه‌ها" value={projects.length} helper="پروژه‌های قابل انتخاب" />
        <StatCard label="نوع محتوا" value={contentTypes.length} helper="قالب‌های محتوایی" />
        <StatCard label="مدل‌ها" value={models.length || "پیش‌فرض"} helper="مدل‌های Ollama" />
        <StatCard label="حالت" value="تکی" helper="تولید دسته‌ای فعلاً غیرفعال است" />
      </section>

      <GenerateContentForm
        apiBaseUrl={API_BASE_URL}
        projects={projects}
        contentTypes={contentTypes}
        models={models}
      />
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/components/generate-content-form.tsx",
    r'''
"use client";

import { FormEvent, useMemo, useState } from "react";

type ProjectOption = {
  id: string;
  name: string;
  status?: string;
  project_type?: string;
};

type ContentTypeOption = {
  key: string;
  label: string;
  description?: string;
};

type ModelOption = {
  name: string;
  provider?: string;
};

type GenerateContentFormProps = {
  apiBaseUrl: string;
  projects: ProjectOption[];
  contentTypes: ContentTypeOption[];
  models: ModelOption[];
};

type GenerationResult = {
  ok: boolean;
  endpoint: string;
  raw: unknown;
  outputText: string;
  assetId?: string;
  message?: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getNestedString(source: unknown, keys: string[]): string {
  let current: unknown = source;

  for (const key of keys) {
    const record = asRecord(current);
    current = record[key];
  }

  return typeof current === "string" ? current : "";
}

function extractOutput(payload: unknown): string {
  const directKeys = [
    "content",
    "text",
    "output",
    "result",
    "body",
    "generated_content",
    "generated_text",
    "message"
  ];

  const record = asRecord(payload);

  for (const key of directKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  const nestedCandidates = [
    ["asset", "body"],
    ["content_asset", "body"],
    ["data", "body"],
    ["data", "content"],
    ["data", "text"],
    ["generation", "content"],
    ["generation", "text"]
  ];

  for (const candidate of nestedCandidates) {
    const value = getNestedString(payload, candidate);
    if (value.trim()) {
      return value;
    }
  }

  return JSON.stringify(payload, null, 2);
}

function extractAssetId(payload: unknown): string | undefined {
  const record = asRecord(payload);
  const directKeys = ["asset_id", "content_asset_id", "id"];

  for (const key of directKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  const nestedCandidates = [
    ["asset", "id"],
    ["content_asset", "id"],
    ["data", "asset_id"],
    ["data", "content_asset_id"],
    ["data", "id"]
  ];

  for (const candidate of nestedCandidates) {
    const value = getNestedString(payload, candidate);
    if (value.trim()) {
      return value;
    }
  }

  return undefined;
}

async function postJson(
  endpoint: string,
  payload: Record<string, unknown>
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  let data: unknown;

  try {
    data = await response.json();
  } catch {
    data = await response.text();
  }

  return {
    ok: response.ok,
    status: response.status,
    data
  };
}

function buildQualityBrief(input: {
  projectName: string;
  contentType: string;
  outputLanguage: string;
  purpose: string;
  audience: string;
  tone: string;
  outputFormat: string;
  qualityLevel: string;
  title: string;
  brief: string;
}) {
  return `
شما دستیار تولید محتوای حرفه‌ای دامامدیا هستید.

زبان خروجی:
${input.outputLanguage}

پروژه:
${input.projectName}

نوع محتوا:
${input.contentType}

عنوان پیشنهادی:
${input.title || "در صورت نیاز، خودت یک عنوان دقیق و مناسب پیشنهاد بده."}

هدف محتوا:
${input.purpose}

مخاطب:
${input.audience}

لحن:
${input.tone}

قالب خروجی:
${input.outputFormat}

سطح کیفیت:
${input.qualityLevel}

دستور کیفیت:
- خروجی باید آماده استفاده باشد، نه فقط ایده خام.
- از جمله‌های کلیشه‌ای، عمومی و تکراری پرهیز کن.
- متن باید ساختار روشن داشته باشد.
- اگر موضوع مربوط به برند، پروژه هنری، سایت، محصول یا ارائه سرمایه‌گذاری است، متن باید حرفه‌ای و قابل ارائه باشد.
- ادعاهای بزرگ و بی‌پشتوانه ننویس.
- متن را با جزئیات کاربردی، اما بدون زیاده‌گویی بنویس.
- اگر خروجی فارسی است، فارسی روان، طبیعی و غیرترجمه‌ای بنویس.
- خروجی را تمیز، منظم و قابل کپی‌کردن ارائه کن.
- از توضیح اضافه درباره اینکه «من یک هوش مصنوعی هستم» خودداری کن.
- فقط خود خروجی نهایی را بنویس مگر اینکه brief خواسته باشد تحلیل هم ارائه شود.

درخواست اصلی کاربر:
${input.brief}
`.trim();
}

export function GenerateContentForm({
  apiBaseUrl,
  projects,
  contentTypes,
  models
}: GenerateContentFormProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [contentType, setContentType] = useState(contentTypes[0]?.key ?? "");
  const [model, setModel] = useState(models[0]?.name ?? "");
  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [outputLanguage, setOutputLanguage] = useState("فارسی");
  const [purpose, setPurpose] = useState("معرفی حرفه‌ای و قابل استفاده");
  const [audience, setAudience] = useState("مخاطب عمومی، سرمایه‌گذار یا کارفرمای بالقوه");
  const [tone, setTone] = useState("حرفه‌ای، روشن، جذاب و غیراغراق‌آمیز");
  const [outputFormat, setOutputFormat] = useState("متن منظم با تیترهای کوتاه");
  const [qualityLevel, setQualityLevel] = useState("کیفیت بالا، آماده استفاده، کم‌کلی‌گویی");
  const [saveOutput, setSaveOutput] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState("");

  const selectedProject = projects.find((project) => project.id === projectId);
  const selectedContentType = contentTypes.find((type) => type.key === contentType);

  const canSubmit = useMemo(() => {
    return Boolean(projectId && contentType && brief.trim() && !isGenerating);
  }, [brief, contentType, isGenerating, projectId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      setError("اول پروژه، نوع محتوا و توضیح کار را وارد کن.");
      return;
    }

    setIsGenerating(true);
    setError("");
    setResult(null);

    const enhancedBrief = buildQualityBrief({
      projectName: selectedProject?.name ?? projectId,
      contentType: selectedContentType?.label ?? contentType,
      outputLanguage,
      purpose,
      audience,
      tone,
      outputFormat,
      qualityLevel,
      title: title.trim(),
      brief: brief.trim()
    });

    const basePayload = {
      project_id: projectId,
      content_type: contentType,
      title: title.trim() || undefined,
      brief: enhancedBrief,
      prompt: enhancedBrief,
      model: model || undefined,
      provider: "ollama",
      save_output: saveOutput
    };

    try {
      const contentEndpoint = `${apiBaseUrl}/content/generate`;
      const contentResponse = await postJson(contentEndpoint, basePayload);

      if (contentResponse.ok) {
        setResult({
          ok: true,
          endpoint: contentEndpoint,
          raw: contentResponse.data,
          outputText: extractOutput(contentResponse.data),
          assetId: extractAssetId(contentResponse.data)
        });
        return;
      }

      const workflowEndpoint = `${apiBaseUrl}/workflows/projects/${projectId}/generate`;
      const workflowResponse = await postJson(workflowEndpoint, {
        content_type: contentType,
        title: title.trim() || undefined,
        brief: enhancedBrief,
        prompt: enhancedBrief,
        model: model || undefined,
        provider: "ollama",
        save_output: saveOutput
      });

      if (workflowResponse.ok) {
        setResult({
          ok: true,
          endpoint: workflowEndpoint,
          raw: workflowResponse.data,
          outputText: extractOutput(workflowResponse.data),
          assetId: extractAssetId(workflowResponse.data)
        });
        return;
      }

      setResult({
        ok: false,
        endpoint: workflowEndpoint,
        raw: workflowResponse.data,
        outputText: extractOutput(workflowResponse.data),
        message: `endpoint اصلی خطا داد: HTTP ${contentResponse.status}. endpoint جایگزین هم خطا داد: HTTP ${workflowResponse.status}.`
      });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "تولید محتوا ناموفق بود.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="generation-grid">
      <form className="panel generation-form" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <p className="eyebrow">فرم ساده تولید</p>
          <h2>چه چیزی می‌خواهی بسازی؟</h2>
        </div>

        <label>
          پروژه
          <select
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
          >
            {projects.length > 0 ? (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            ) : (
              <option value="">پروژه‌ای پیدا نشد</option>
            )}
          </select>
        </label>

        <label>
          نوع محتوا
          <select
            value={contentType}
            onChange={(event) => setContentType(event.target.value)}
          >
            {contentTypes.length > 0 ? (
              contentTypes.map((type) => (
                <option key={type.key} value={type.key}>
                  {type.label}
                </option>
              ))
            ) : (
              <option value="">نوع محتوا پیدا نشد</option>
            )}
          </select>
        </label>

        <label>
          مدل
          <select value={model} onChange={(event) => setModel(event.target.value)}>
            {models.length > 0 ? (
              models.map((modelOption) => (
                <option key={modelOption.name} value={modelOption.name}>
                  {modelOption.name}
                </option>
              ))
            ) : (
              <option value="">مدل پیش‌فرض بک‌اند</option>
            )}
          </select>
        </label>

        <label>
          زبان خروجی
          <select
            value={outputLanguage}
            onChange={(event) => setOutputLanguage(event.target.value)}
          >
            <option value="فارسی">فارسی</option>
            <option value="English">English</option>
            <option value="العربية">العربية</option>
            <option value="اردو">اردو</option>
          </select>
        </label>

        <label>
          هدف محتوا
          <input
            value={purpose}
            onChange={(event) => setPurpose(event.target.value)}
            placeholder="مثلاً معرفی، فروش، پیچ سرمایه‌گذاری، متن سایت"
          />
        </label>

        <label>
          مخاطب
          <input
            value={audience}
            onChange={(event) => setAudience(event.target.value)}
            placeholder="مثلاً سرمایه‌گذار، مشتری، کودک و نوجوان، مدیر سایت"
          />
        </label>

        <label>
          لحن
          <input
            value={tone}
            onChange={(event) => setTone(event.target.value)}
            placeholder="مثلاً حرفه‌ای، صمیمی، سینمایی، ساده، تجاری"
          />
        </label>

        <label>
          قالب خروجی
          <input
            value={outputFormat}
            onChange={(event) => setOutputFormat(event.target.value)}
            placeholder="مثلاً متن کوتاه، مقاله، تیتر و پاراگراف، جدول"
          />
        </label>

        <label>
          سطح کیفیت
          <select
            value={qualityLevel}
            onChange={(event) => setQualityLevel(event.target.value)}
          >
            <option value="کیفیت بالا، آماده استفاده، کم‌کلی‌گویی">
              کیفیت بالا و آماده استفاده
            </option>
            <option value="خلاصه، دقیق، سریع و قابل کپی">
              خلاصه و سریع
            </option>
            <option value="حرفه‌ای، پرجزئیات، مناسب ارائه رسمی">
              رسمی و پرجزئیات
            </option>
            <option value="خلاقانه، تصویری، مناسب پروژه هنری و داستانی">
              خلاقانه و داستانی
            </option>
            <option value="تجاری، قانع‌کننده، مناسب فروش و بازاریابی">
              تجاری و بازاریابی
            </option>
          </select>
        </label>

        <label>
          عنوان اختیاری
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="مثلاً معرفی پروژه گرگران"
          />
        </label>

        <label>
          توضیح کار
          <textarea
            value={brief}
            onChange={(event) => setBrief(event.target.value)}
            rows={8}
            placeholder="اینجا دقیق بنویس چه محتوایی می‌خواهی..."
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={saveOutput}
            onChange={(event) => setSaveOutput(event.target.checked)}
          />
          <span>save_output  خروجی تولیدشده ذخیره شود</span>
        </label>

        {error ? <p className="form-error">{error}</p> : null}

        <button type="submit" disabled={!canSubmit}>
          {isGenerating ? "در حال تولید..." : "تولید محتوا"}
        </button>
      </form>

      <section className="panel generation-output">
        <div className="panel-heading">
          <p className="eyebrow">خروجی</p>
          <h2>نتیجه تولید</h2>
        </div>

        {result ? (
          <>
            <div className="health-list">
              <div>
                <strong>وضعیت</strong>
                <span>{result.ok ? "تولید شد" : "خطا در تولید"}</span>
              </div>
              <div>
                <strong>مسیر استفاده‌شده</strong>
                <span>{result.endpoint}</span>
              </div>
              {result.message ? (
                <div>
                  <strong>پیام</strong>
                  <span>{result.message}</span>
                </div>
              ) : null}
              {result.assetId ? (
                <div>
                  <strong>محتوای ذخیره‌شده</strong>
                  <a href={`/content-assets/${result.assetId}`}>
                    باز کردن محتوا
                  </a>
                </div>
              ) : null}
            </div>

            <pre className="generated-output">{result.outputText}</pre>

            <details>
              <summary>پاسخ خام سیستم</summary>
              <pre className="json-block">{JSON.stringify(result.raw, null, 2)}</pre>
            </details>
          </>
        ) : (
          <div className="quality-help">
            <h3>برای خروجی بهتر</h3>
            <p>به‌جای یک جمله کوتاه، این‌ها را مشخص کن:</p>
            <ul>
              <li>این متن برای چه کسی است؟</li>
              <li>کجا استفاده می‌شود؟ سایت، پیچ، محصول، شبکه اجتماعی؟</li>
              <li>لحن باید رسمی باشد یا صمیمی؟</li>
              <li>خروجی کوتاه می‌خواهی یا کامل؟</li>
              <li>چه چیزهایی حتماً باید در متن بیاید؟</li>
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Persian simple operator UX */",
    r'''
/* Persian simple operator UX */
html,
body {
  direction: rtl;
}

body {
  text-align: right;
}

.app-nav {
  direction: rtl;
}

.actions,
.stats-grid,
.simple-start-grid,
.generation-grid,
.two-column {
  direction: rtl;
}

pre,
code,
.json-block,
.generated-output {
  direction: rtl;
  text-align: right;
}

.responsive-table table {
  direction: rtl;
}

.responsive-table th,
.responsive-table td {
  text-align: right;
}

.simple-start-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.simple-start-card {
  display: grid;
  gap: 0.75rem;
  padding: 1.35rem;
  border: 1px solid var(--border);
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.62);
  color: var(--text);
  text-decoration: none;
}

.simple-start-card span {
  display: inline-flex;
  width: 2.2rem;
  height: 2.2rem;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--text);
  color: var(--surface);
  font-weight: 900;
}

.simple-start-card strong {
  font-size: 1.1rem;
}

.simple-start-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.simple-help-panel {
  margin-top: 1rem;
}

.simple-steps {
  display: grid;
  gap: 0.75rem;
  color: var(--muted);
  line-height: 1.9;
}

.quality-help {
  display: grid;
  gap: 0.75rem;
  color: var(--muted);
  line-height: 1.9;
}

.quality-help h3 {
  color: var(--text);
  margin: 0;
}

.quality-help p {
  margin: 0;
}

.quality-help ul {
  display: grid;
  gap: 0.5rem;
}

@media (max-width: 1100px) {
  .simple-start-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .simple-start-grid {
    grid-template-columns: 1fr;
  }
}
    ''',
)


write_file(
    "docs/persian-simple-ux-and-quality-generation.md",
    r'''
# Persian Simple UX and Quality Generation

Release Pack V makes the operator-facing frontend easier to use in Persian and improves generation quality.

## UX Changes

- Persian navigation labels
- Persian dashboard
- simpler project list
- clearer workflow from project creation to generation
- Persian Generate page
- Persian generation form

## Quality Generation Changes

The Generate form now wraps the user brief with a stronger quality instruction.

It adds:

- output language
- project name
- content type
- purpose
- audience
- tone
- output format
- quality level
- anti-generic writing checklist
- final-output-only instruction

## Safety

Still safe:

- one generation at a time
- no batch execution
- no delete
- no publishing
- save_output remains explicit
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack V Completed",
    r'''
## Release Pack V Completed

Name:

Persian Simple UX + Quality Generation

Added files:

- docs/persian-simple-ux-and-quality-generation.md

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/app/page.tsx
- frontend/src/app/projects/page.tsx
- frontend/src/app/generate/page.tsx
- frontend/src/components/generate-content-form.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- Persian operator navigation
- Persian simple dashboard
- Persian project list
- Persian generation form
- quality-focused prompt wrapper
- audience/tone/purpose/output-format fields
- safer high-quality generation defaults

Next recommended Release Pack:

Release Pack W: Project Workspace Polish

Suggested scope:

- make each project page simpler and Persian
- show project assets inside project page
- add direct generate-for-this-project button
- add recent outputs panel
- add export shortcuts
    ''',
)

print("Release Pack V applied successfully.")
