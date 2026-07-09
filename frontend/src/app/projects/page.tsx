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
