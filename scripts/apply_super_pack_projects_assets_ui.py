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
const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/content-assets", label: "Content Assets" }
];

export function AppNav() {
  return (
    <nav className="app-nav">
      <a className="brand-link" href="/">
        DAMA
      </a>

      <div>
        {navItems.map((item) => (
          <a key={item.href} href={item.href}>
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
    ''',
)


write_file(
    "frontend/src/components/status-pill.tsx",
    r'''
type StatusPillProps = {
  status?: string;
};

export function StatusPill({ status = "unknown" }: StatusPillProps) {
  return <span className="status-pill">{status}</span>;
}
    ''',
)


write_file(
    "frontend/src/components/data-table.tsx",
    r'''
import { StatusPill } from "./status-pill";

type Column<T> = {
  key: string;
  label: string;
  render: (item: T) => React.ReactNode;
};

type DataTableProps<T> = {
  columns: Column<T>[];
  items: T[];
  emptyLabel: string;
};

export function DataTable<T>({ columns, items, emptyLabel }: DataTableProps<T>) {
  if (items.length === 0) {
    return <p className="empty-state">{emptyLabel}</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key}>{column.render(item)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { StatusPill };
    ''',
)


write_file(
    "frontend/src/lib/types.ts",
    r'''
export type DamaError = {
  error: {
    type: "http_error" | "validation_error";
    status_code: number;
    message: string;
    path: string;
    details?: unknown[];
  };
};

export type Project = {
  id: string;
  name: string;
  slug?: string;
  project_type: string;
  language?: string;
  description?: string;
  status: string;
  content_types?: string[];
  created_at?: string;
  updated_at?: string;
};

export type ContentAsset = {
  id: string;
  project_id: string;
  content_type: string;
  title: string;
  body?: string;
  status: string;
  source: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type ProjectSummary = {
  project: Project;
  total_assets: number;
  assets_by_status: Record<string, number>;
  assets_by_content_type: Record<string, number>;
  recent_assets: ContentAsset[];
};

export type ProjectContentAssetsResponse = {
  project_id: string;
  content_assets: ContentAsset[];
};

export type DashboardSummary = {
  system: Record<string, unknown>;
  projects: {
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    recent: Project[];
  };
  content_assets: {
    total: number;
    by_status: Record<string, number>;
    by_content_type: Record<string, number>;
    by_source: Record<string, number>;
    recent: ContentAsset[];
  };
  exports: {
    total_markdown_files: number;
    export_root: string;
    recent: unknown[];
  };
  readiness: {
    has_projects: boolean;
    has_content_assets: boolean;
    has_exports: boolean;
    dashboard_ready: boolean;
    workflow_ready: boolean;
    export_ready: boolean;
  };
};

export type FrontendContract = {
  name: string;
  version: string;
  backend_base_url: string;
  interactive_docs: string;
  openapi_json: string;
  recommended_frontend_sections: Array<{
    key: string;
    title: string;
    primary_endpoints: string[];
  }>;
  endpoint_count: number;
};
    ''',
)


write_file(
    "frontend/src/lib/api-client.ts",
    r'''
import type {
  ContentAsset,
  DashboardSummary,
  FrontendContract,
  Project,
  ProjectContentAssetsResponse,
  ProjectSummary
} from "./types";

export const DAMA_API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${DAMA_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(JSON.stringify(data));
  }

  return data as T;
}

function normalizeListResponse<T>(data: unknown, possibleKeys: string[]): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }

  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;

    for (const key of possibleKeys) {
      const value = record[key];

      if (Array.isArray(value)) {
        return value as T[];
      }
    }
  }

  return [];
}

export const damaApi = {
  dashboardSummary(): Promise<DashboardSummary> {
    return requestJson<DashboardSummary>("/dashboard/summary");
  },

  frontendContract(): Promise<FrontendContract> {
    return requestJson<FrontendContract>("/developer/frontend-contract");
  },

  endpointMap(): Promise<unknown> {
    return requestJson<unknown>("/developer/endpoint-map");
  },

  runbook(): Promise<unknown> {
    return requestJson<unknown>("/developer/runbook");
  },

  async projects(): Promise<Project[]> {
    const data = await requestJson<unknown>("/projects");
    return normalizeListResponse<Project>(data, ["projects", "items", "results"]);
  },

  project(projectId: string): Promise<Project> {
    return requestJson<Project>(`/projects/${projectId}`);
  },

  projectSummary(projectId: string): Promise<ProjectSummary> {
    return requestJson<ProjectSummary>(`/projects/${projectId}/summary`);
  },

  projectContentAssets(projectId: string): Promise<ProjectContentAssetsResponse> {
    return requestJson<ProjectContentAssetsResponse>(
      `/projects/${projectId}/content-assets`
    );
  },

  async contentAssets(): Promise<ContentAsset[]> {
    const data = await requestJson<unknown>("/content-assets");
    return normalizeListResponse<ContentAsset>(data, [
      "content_assets",
      "assets",
      "items",
      "results"
    ]);
  }
};
    ''',
)


write_file(
    "frontend/src/app/layout.tsx",
    r'''
import { AppNav } from "../components/app-nav";
import "./globals.css";

export const metadata = {
  title: "DAMA Dashboard",
  description: "AI Content Automation Platform dashboard"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppNav />
        {children}
      </body>
    </html>
  );
}
    ''',
)


write_file(
    "frontend/src/app/projects/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../components/data-table";
import { StatCard } from "../../components/stat-card";
import { damaApi } from "../../lib/api-client";
import type { Project } from "../../lib/types";

async function loadProjects(): Promise<Project[]> {
  try {
    return await damaApi.projects();
  } catch {
    return [];
  }
}

export default async function ProjectsPage() {
  const projects = await loadProjects();

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Projects</p>
        <h1>Project workspace</h1>
        <p className="lead">
          Browse DAMA projects and open project summaries for content workflow management.
        </p>
      </section>

      <section className="stats-grid">
        <StatCard label="Projects" value={projects.length} helper="Loaded from backend" />
        <StatCard
          label="Active"
          value={projects.filter((project) => project.status === "active").length}
          helper="Active project records"
        />
        <StatCard
          label="Draft"
          value={projects.filter((project) => project.status === "draft").length}
          helper="Draft project records"
        />
        <StatCard
          label="Types"
          value={new Set(projects.map((project) => project.project_type)).size}
          helper="Unique project types"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Project List</p>
          <h2>All projects</h2>
        </div>

        <DataTable<Project>
          emptyLabel="No projects found."
          items={projects}
          columns={[
            {
              key: "name",
              label: "Name",
              render: (project) => (
                <a className="table-link" href={`/projects/${project.id}`}>
                  {project.name}
                </a>
              )
            },
            {
              key: "type",
              label: "Type",
              render: (project) => project.project_type
            },
            {
              key: "language",
              label: "Language",
              render: (project) => project.language ?? "—"
            },
            {
              key: "status",
              label: "Status",
              render: (project) => <StatusPill status={project.status} />
            }
          ]}
        />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/projects/[projectId]/page.tsx",
    r'''
import { CountBreakdown } from "../../../components/count-breakdown";
import { RecentList } from "../../../components/recent-list";
import { StatCard } from "../../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../../lib/api-client";
import type { Project, ProjectSummary } from "../../../lib/types";

type ProjectDetailPageProps = {
  params: {
    projectId: string;
  };
};

async function loadProject(projectId: string): Promise<Project | null> {
  try {
    return await damaApi.project(projectId);
  } catch {
    return null;
  }
}

async function loadProjectSummary(projectId: string): Promise<ProjectSummary | null> {
  try {
    return await damaApi.projectSummary(projectId);
  } catch {
    return null;
  }
}

export default async function ProjectDetailPage({ params }: ProjectDetailPageProps) {
  const [project, summary] = await Promise.all([
    loadProject(params.projectId),
    loadProjectSummary(params.projectId)
  ]);

  if (!project) {
    return (
      <main className="page-shell">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Project</p>
            <h1>Project not found</h1>
          </div>
          <p className="empty-state">
            The selected project could not be loaded from the backend.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Project Detail</p>
        <h1>{project.name}</h1>
        <p className="lead">
          {project.description || "Project workflow and content asset overview."}
        </p>

        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/projects/${project.id}/summary`}>
            Raw Summary
          </a>
          <a href={`${DAMA_API_BASE_URL}/workflows/projects/${project.id}/output-plan`}>
            Output Plan
          </a>
          <a href={`${DAMA_API_BASE_URL}/exports/projects/${project.id}/bundle`}>
            Export Endpoint
          </a>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="Status" value={project.status} helper="Project state" />
        <StatCard label="Type" value={project.project_type} helper="Project type" />
        <StatCard label="Language" value={project.language ?? "—"} helper="Project language" />
        <StatCard
          label="Assets"
          value={summary?.total_assets ?? 0}
          helper="Connected content assets"
        />
      </section>

      {summary ? (
        <>
          <section className="breakdown-grid two-card-grid">
            <CountBreakdown title="Assets by status" items={summary.assets_by_status} />
            <CountBreakdown title="Assets by content type" items={summary.assets_by_content_type} />
          </section>

          <RecentList
            eyebrow="Content"
            title="Recent project assets"
            emptyLabel="No content assets for this project yet."
            items={summary.recent_assets}
          />
        </>
      ) : (
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Summary</p>
            <h2>Summary unavailable</h2>
          </div>
          <p className="empty-state">
            Project loaded, but the summary endpoint did not return data.
          </p>
        </section>
      )}
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/content-assets/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../components/data-table";
import { StatCard } from "../../components/stat-card";
import { damaApi } from "../../lib/api-client";
import type { ContentAsset } from "../../lib/types";

async function loadContentAssets(): Promise<ContentAsset[]> {
  try {
    return await damaApi.contentAssets();
  } catch {
    return [];
  }
}

export default async function ContentAssetsPage() {
  const assets = await loadContentAssets();

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Content Assets</p>
        <h1>Content asset library</h1>
        <p className="lead">
          Browse manual and AI-generated content assets stored inside DAMA.
        </p>
      </section>

      <section className="stats-grid">
        <StatCard label="Assets" value={assets.length} helper="Total loaded assets" />
        <StatCard
          label="AI Generated"
          value={assets.filter((asset) => asset.source === "ai_generated").length}
          helper="Generated by AI workflows"
        />
        <StatCard
          label="Manual"
          value={assets.filter((asset) => asset.source === "manual").length}
          helper="Manual content records"
        />
        <StatCard
          label="Types"
          value={new Set(assets.map((asset) => asset.content_type)).size}
          helper="Unique content types"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Library</p>
          <h2>All content assets</h2>
        </div>

        <DataTable<ContentAsset>
          emptyLabel="No content assets found."
          items={assets}
          columns={[
            {
              key: "title",
              label: "Title",
              render: (asset) => asset.title
            },
            {
              key: "content_type",
              label: "Type",
              render: (asset) => asset.content_type
            },
            {
              key: "source",
              label: "Source",
              render: (asset) => asset.source
            },
            {
              key: "status",
              label: "Status",
              render: (asset) => <StatusPill status={asset.status} />
            }
          ]}
        />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/globals.css",
    r'''
:root {
  color-scheme: light;
  --background: #f7f2ea;
  --surface: #fffaf2;
  --surface-strong: #ffffff;
  --text: #2f2a24;
  --muted: #75695d;
  --border: #e4d8c9;
  --accent: #9a5b2f;
  --accent-soft: #ead3bd;
  --success: #4f7d49;
  --warning: #9a6b2f;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background:
    radial-gradient(circle at top left, rgba(154, 91, 47, 0.12), transparent 32rem),
    var(--background);
  color: var(--text);
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}

a {
  color: inherit;
}

.app-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  width: min(1180px, calc(100% - 32px));
  margin: 16px auto 0;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 250, 242, 0.88);
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 50px rgba(47, 42, 36, 0.06);
}

.app-nav div {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.app-nav a {
  padding: 10px 14px;
  border-radius: 999px;
  text-decoration: none;
  color: var(--muted);
  font-weight: 800;
}

.app-nav a:hover,
.app-nav .brand-link {
  background: var(--surface-strong);
  color: var(--accent);
}

.page-shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 72px;
}

.hero,
.panel,
.stat-card,
.breakdown-card,
.link-card,
.page-heading {
  border: 1px solid var(--border);
  background: rgba(255, 250, 242, 0.88);
  box-shadow: 0 24px 80px rgba(47, 42, 36, 0.06);
  backdrop-filter: blur(8px);
}

.hero,
.page-heading {
  padding: 40px;
  border-radius: 28px;
}

.dashboard-hero {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: 24px;
  align-items: stretch;
}

.hero-status {
  display: grid;
  align-content: center;
  padding: 24px;
  border-radius: 24px;
  background: var(--surface-strong);
  border: 1px solid var(--border);
}

.hero-status span {
  color: var(--success);
  font-weight: 800;
}

.hero-status strong {
  margin-top: 12px;
  font-size: 56px;
  line-height: 1;
}

.hero-status p {
  margin: 8px 0 0;
  color: var(--muted);
}

.eyebrow {
  margin: 0 0 12px;
  color: var(--accent);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1 {
  max-width: 780px;
  margin: 0;
  font-size: clamp(42px, 7vw, 76px);
  line-height: 0.95;
}

h2,
h3,
p {
  overflow-wrap: anywhere;
}

.lead {
  max-width: 760px;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 20px;
  line-height: 1.7;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.actions a {
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: white;
  text-decoration: none;
  font-weight: 800;
}

.stats-grid,
.breakdown-grid,
.link-grid,
.readiness-grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 24px;
}

.stat-card {
  display: grid;
  gap: 8px;
  padding: 24px;
  border-radius: 22px;
}

.stat-card p,
.stat-card span {
  margin: 0;
  color: var(--muted);
}

.stat-card strong {
  font-size: 32px;
  line-height: 1;
}

.panel {
  margin-top: 24px;
  padding: 28px;
  border-radius: 24px;
}

.panel-heading h2 {
  margin: 0;
  font-size: 28px;
}

.readiness-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 20px;
}

.readiness-item {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 18px;
  background: #fff7ec;
  border: 1px solid var(--border);
}

.readiness-item span {
  color: var(--warning);
  font-weight: 800;
}

.readiness-item.is-ready span {
  color: var(--success);
}

.breakdown-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 24px;
}

.two-card-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.breakdown-card {
  padding: 22px;
  border-radius: 20px;
}

.breakdown-card h3 {
  margin: 0 0 16px;
}

.breakdown-card ul {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.breakdown-card li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
}

.breakdown-card li strong {
  color: var(--text);
}

.two-column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.recent-list {
  display: grid;
  gap: 12px;
  margin-top: 20px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: var(--surface-strong);
}

.recent-item h3 {
  margin: 0;
  font-size: 16px;
}

.recent-item p {
  margin: 6px 0 0;
  color: var(--muted);
}

.status-pill,
.recent-item span {
  display: inline-flex;
  height: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
}

.empty-state {
  margin: 16px 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.code-block {
  margin-top: 16px;
  padding: 16px;
  overflow-x: auto;
  border-radius: 16px;
  background: #2f2a24;
  color: #fffaf2;
}

.link-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 20px;
}

.link-card {
  display: block;
  padding: 20px;
  border-radius: 18px;
  text-decoration: none;
}

.link-card span {
  font-weight: 900;
}

.link-card p {
  margin: 10px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.table-wrap {
  width: 100%;
  margin-top: 20px;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

.data-table th,
.data-table td {
  padding: 14px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: top;
}

.data-table th {
  color: var(--muted);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.table-link {
  color: var(--accent);
  font-weight: 900;
  text-decoration: none;
}

@media (max-width: 980px) {
  .dashboard-hero,
  .two-column {
    grid-template-columns: 1fr;
  }

  .stats-grid,
  .breakdown-grid,
  .link-grid,
  .readiness-grid,
  .two-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .app-nav {
    align-items: flex-start;
    border-radius: 24px;
    flex-direction: column;
  }

  .hero,
  .panel,
  .page-heading {
    padding: 24px;
  }

  .stats-grid,
  .breakdown-grid,
  .link-grid,
  .readiness-grid,
  .two-card-grid {
    grid-template-columns: 1fr;
  }
}
    ''',
)


write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RequiredFiles = @(
    ".\frontend\README.md",
    ".\frontend\package.json",
    ".\frontend\next.config.mjs",
    ".\frontend\tsconfig.json",
    ".\frontend\src\app\layout.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\projects\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx",
    ".\frontend\src\components\data-table.tsx",
    ".\frontend\src\components\status-pill.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$DashboardPage = Get-Content ".\frontend\src\app\page.tsx" -Raw
$ProjectsPage = Get-Content ".\frontend\src\app\projects\page.tsx" -Raw
$AssetsPage = Get-Content ".\frontend\src\app\content-assets\page.tsx" -Raw

if ($ApiClient -notmatch "projects") {
    throw "API client does not expose projects."
}

if ($ApiClient -notmatch "contentAssets") {
    throw "API client does not expose contentAssets."
}

if ($DashboardPage -notmatch "dashboardSummary") {
    throw "Dashboard page does not use dashboardSummary API client."
}

if ($ProjectsPage -notmatch "damaApi.projects") {
    throw "Projects page does not use projects API client."
}

if ($AssetsPage -notmatch "damaApi.contentAssets") {
    throw "Content assets page does not use contentAssets API client."
}

Write-Host "Frontend UI check passed."
    ''',
)


write_file(
    "docs/frontend-routes.md",
    r'''
# DAMA Frontend Routes

Super Pack J adds initial application routes.

## Routes

    /
    /projects
    /projects/[projectId]
    /content-assets

## Route Purpose

## /

Dashboard summary and developer quick links.

## /projects

Project list and basic project stats.

## /projects/[projectId]

Project detail shell, project summary, asset breakdowns, and workflow links.

## /content-assets

Content asset library with basic stats.

## Shared Components

- AppNav
- StatCard
- ReadinessPanel
- RecentList
- CountBreakdown
- LinkCard
- DataTable
- StatusPill

## API Client Coverage

The frontend API client now covers:

- dashboard summary
- frontend contract
- endpoint map
- runbook
- project list
- project detail
- project summary
- project content assets
- content asset list
    ''',
)


append_once(
    "docs/frontend-foundation.md",
    "## Projects and Content Assets UI",
    r'''
## Projects and Content Assets UI

Super Pack J adds application routes for project and content asset management.

Added routes:

- /
- /projects
- /projects/[projectId]
- /content-assets

Added shared UI:

- AppNav
- DataTable
- StatusPill
    ''',
)


append_once(
    "docs/project-status.md",
    "## Super Pack J Completed",
    r'''
## Super Pack J Completed

Name:

Projects UI + Content Assets UI

Added files:

- frontend/src/components/app-nav.tsx
- frontend/src/components/status-pill.tsx
- frontend/src/components/data-table.tsx
- frontend/src/app/projects/page.tsx
- frontend/src/app/projects/[projectId]/page.tsx
- frontend/src/app/content-assets/page.tsx
- docs/frontend-routes.md

Updated files:

- frontend/src/app/layout.tsx
- frontend/src/app/globals.css
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- scripts/frontend-check.ps1
- docs/frontend-foundation.md
- docs/project-status.md

Added behavior:

- frontend navigation
- project list UI
- project detail UI shell
- content asset library UI
- frontend API client extensions
- stronger frontend structure checks

Purpose:

Move DAMA frontend from dashboard-only to an initial multi-page application shell.

Next recommended Super Pack:

Super Pack K: Workflow UI + Export UI + Maintenance UI

Suggested scope:

- workflow page
- output plan viewer
- batch dry-run form shell
- export links
- maintenance status page
- backup trigger note or safe manual link
    ''',
)

print("Super Pack J applied successfully.")
