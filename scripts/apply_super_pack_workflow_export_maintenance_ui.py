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
  { href: "/content-assets", label: "Content Assets" },
  { href: "/workflows", label: "Workflows" },
  { href: "/exports", label: "Exports" },
  { href: "/maintenance", label: "Maintenance" }
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
    "frontend/src/components/action-card.tsx",
    r'''
type ActionCardProps = {
  title: string;
  description: string;
  href?: string;
  label?: string;
};

export function ActionCard({ title, description, href, label = "Open" }: ActionCardProps) {
  const content = (
    <>
      <span>{title}</span>
      <p>{description}</p>
      <strong>{label}</strong>
    </>
  );

  if (href) {
    return (
      <a className="action-card" href={href}>
        {content}
      </a>
    );
  }

  return <article className="action-card">{content}</article>;
}
    ''',
)


write_file(
    "frontend/src/components/json-preview.tsx",
    r'''
type JsonPreviewProps = {
  title: string;
  data: unknown;
};

export function JsonPreview({ title, data }: JsonPreviewProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">JSON</p>
        <h2>{title}</h2>
      </div>

      <pre className="code-block">{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}
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

export type PlannedOutput = {
  order: number;
  project_id: string;
  content_type: string;
  title: string;
  workflow_stage: string;
  recommended_status: string;
  generation_topic: string;
};

export type OutputPlanResponse = {
  project_id: string;
  planned_outputs: PlannedOutput[];
};

export type MaintenanceStatus = {
  database: {
    path: string;
    exists: boolean;
    size_bytes: number;
    tables: Record<string, number>;
  };
  exports: {
    path: string;
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    recent: Array<{
      file_name: string;
      file_path: string;
      size_bytes: number;
    }>;
  };
  backups: {
    path: string;
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    recent: Array<{
      file_name: string;
      file_path: string;
      size_bytes: number;
    }>;
  };
  maintenance_ready: boolean;
  generated_at: string;
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
    recent: Array<{
      file_name?: string;
      file_path?: string;
      size_bytes?: number;
    }>;
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
  MaintenanceStatus,
  OutputPlanResponse,
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

  maintenanceStatus(): Promise<MaintenanceStatus> {
    return requestJson<MaintenanceStatus>("/maintenance/status");
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

  projectOutputPlan(projectId: string): Promise<OutputPlanResponse> {
    return requestJson<OutputPlanResponse>(
      `/workflows/projects/${projectId}/output-plan`
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
    "frontend/src/app/workflows/page.tsx",
    r'''
import { ActionCard } from "../../components/action-card";
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

export default async function WorkflowsPage() {
  const projects = await loadProjects();

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Workflows</p>
        <h1>Workflow control room</h1>
        <p className="lead">
          Review project output plans, prepare draft assets, and run safer batch generation workflows.
        </p>
      </section>

      <section className="stats-grid">
        <StatCard label="Projects" value={projects.length} helper="Workflow-ready project records" />
        <StatCard
          label="Active"
          value={projects.filter((project) => project.status === "active").length}
          helper="Active workflows"
        />
        <StatCard
          label="Draft"
          value={projects.filter((project) => project.status === "draft").length}
          helper="Draft workflows"
        />
        <StatCard
          label="Workflow API"
          value="Ready"
          helper="Output plan and batch endpoints"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Output Plan"
          description="Open a project workflow page to inspect planned outputs."
          label="Select project below"
        />
        <ActionCard
          title="Draft Assets"
          description="Backend supports creating draft content assets from project plans."
          label="API ready"
        />
        <ActionCard
          title="Batch Dry Run"
          description="Backend supports dry-run planning before AI generation."
          label="Safe first"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Projects</p>
          <h2>Select a workflow project</h2>
        </div>

        <DataTable<Project>
          emptyLabel="No projects found."
          items={projects}
          columns={[
            {
              key: "name",
              label: "Name",
              render: (project) => (
                <a className="table-link" href={`/workflows/${project.id}`}>
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
              key: "status",
              label: "Status",
              render: (project) => <StatusPill status={project.status} />
            },
            {
              key: "assets",
              label: "Project",
              render: (project) => (
                <a className="table-link" href={`/projects/${project.id}`}>
                  Detail
                </a>
              )
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
    "frontend/src/app/workflows/[projectId]/page.tsx",
    r'''
import { ActionCard } from "../../../components/action-card";
import { DataTable, StatusPill } from "../../../components/data-table";
import { JsonPreview } from "../../../components/json-preview";
import { StatCard } from "../../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../../lib/api-client";
import type { OutputPlanResponse, PlannedOutput, Project } from "../../../lib/types";

type WorkflowProjectPageProps = {
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

async function loadOutputPlan(projectId: string): Promise<OutputPlanResponse | null> {
  try {
    return await damaApi.projectOutputPlan(projectId);
  } catch {
    return null;
  }
}

export default async function WorkflowProjectPage({ params }: WorkflowProjectPageProps) {
  const [project, outputPlan] = await Promise.all([
    loadProject(params.projectId),
    loadOutputPlan(params.projectId)
  ]);

  if (!project) {
    return (
      <main className="page-shell">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Workflow</p>
            <h1>Project not found</h1>
          </div>
          <p className="empty-state">The selected workflow project could not be loaded.</p>
        </section>
      </main>
    );
  }

  const plannedOutputs = outputPlan?.planned_outputs ?? [];

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Project Workflow</p>
        <h1>{project.name}</h1>
        <p className="lead">
          Output planning and safe workflow operations for this project.
        </p>

        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/workflows/projects/${project.id}/output-plan`}>
            Raw Output Plan
          </a>
          <a href={`${DAMA_API_BASE_URL}/projects/${project.id}/summary`}>
            Project Summary
          </a>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard label="Planned Outputs" value={plannedOutputs.length} helper="From project content types" />
        <StatCard label="Project Status" value={project.status} helper="Current workflow status" />
        <StatCard label="Project Type" value={project.project_type} helper="Workflow template" />
        <StatCard label="Language" value={project.language ?? "—"} helper="Generation language" />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Create Draft Assets"
          description="Use the backend endpoint to create draft content assets from this output plan."
          href={`${DAMA_API_BASE_URL}/workflows/projects/${project.id}/draft-assets`}
          label="POST endpoint"
        />
        <ActionCard
          title="Batch Generate"
          description="Run batch generation with dry_run=true first to avoid unsafe execution."
          href={`${DAMA_API_BASE_URL}/workflows/projects/${project.id}/batch-generate`}
          label="POST endpoint"
        />
        <ActionCard
          title="Export Bundle"
          description="Export all project content assets as a Markdown bundle."
          href={`${DAMA_API_BASE_URL}/exports/projects/${project.id}/bundle`}
          label="POST endpoint"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Output Plan</p>
          <h2>Planned outputs</h2>
        </div>

        <DataTable<PlannedOutput>
          emptyLabel="No planned outputs found."
          items={plannedOutputs}
          columns={[
            {
              key: "order",
              label: "Order",
              render: (item) => item.order
            },
            {
              key: "title",
              label: "Title",
              render: (item) => item.title
            },
            {
              key: "type",
              label: "Type",
              render: (item) => item.content_type
            },
            {
              key: "stage",
              label: "Stage",
              render: (item) => <StatusPill status={item.workflow_stage} />
            }
          ]}
        />
      </section>

      <JsonPreview title="Output plan payload" data={outputPlan ?? { planned_outputs: [] }} />
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/exports/page.tsx",
    r'''
import { ActionCard } from "../../components/action-card";
import { DataTable } from "../../components/data-table";
import { StatCard } from "../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../lib/api-client";
import type { DashboardSummary, Project } from "../../lib/types";

async function loadDashboardSummary(): Promise<DashboardSummary | null> {
  try {
    return await damaApi.dashboardSummary();
  } catch {
    return null;
  }
}

async function loadProjects(): Promise<Project[]> {
  try {
    return await damaApi.projects();
  } catch {
    return [];
  }
}

export default async function ExportsPage() {
  const [summary, projects] = await Promise.all([
    loadDashboardSummary(),
    loadProjects()
  ]);

  const recentExports = summary?.exports.recent ?? [];

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Exports</p>
        <h1>Markdown export center</h1>
        <p className="lead">
          Review local export status and access project bundle export endpoints.
        </p>
      </section>

      <section className="stats-grid">
        <StatCard
          label="Markdown Files"
          value={summary?.exports.total_markdown_files ?? 0}
          helper="Local export count"
        />
        <StatCard
          label="Projects"
          value={projects.length}
          helper="Available for bundle export"
        />
        <StatCard
          label="Export Ready"
          value={summary?.readiness.export_ready ? "Ready" : "Pending"}
          helper="Based on content assets"
        />
        <StatCard
          label="Export Root"
          value={summary?.exports.export_root ? "Set" : "—"}
          helper="Backend export directory"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Project Bundle"
          description="Each project can be exported as a Markdown bundle through a POST endpoint."
          label="Available"
        />
        <ActionCard
          title="Content Asset Markdown"
          description="Single content assets can also be exported as Markdown files."
          label="Available"
        />
        <ActionCard
          title="Local Files"
          description="Generated export files stay local and are ignored by Git."
          label="Safe"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Recent Exports</p>
          <h2>Local Markdown files</h2>
        </div>

        <DataTable
          emptyLabel="No export files found."
          items={recentExports}
          columns={[
            {
              key: "file",
              label: "File",
              render: (item) => item.file_name ?? "Unknown"
            },
            {
              key: "size",
              label: "Size",
              render: (item) => `${item.size_bytes ?? 0} bytes`
            },
            {
              key: "path",
              label: "Path",
              render: (item) => item.file_path ?? "—"
            }
          ]}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Project Bundles</p>
          <h2>Export endpoints</h2>
        </div>

        <DataTable<Project>
          emptyLabel="No projects found."
          items={projects}
          columns={[
            {
              key: "name",
              label: "Project",
              render: (project) => project.name
            },
            {
              key: "type",
              label: "Type",
              render: (project) => project.project_type
            },
            {
              key: "endpoint",
              label: "Export Endpoint",
              render: (project) => (
                <a className="table-link" href={`${DAMA_API_BASE_URL}/exports/projects/${project.id}/bundle`}>
                  POST bundle
                </a>
              )
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
    "frontend/src/app/maintenance/page.tsx",
    r'''
import { ActionCard } from "../../components/action-card";
import { CountBreakdown } from "../../components/count-breakdown";
import { DataTable } from "../../components/data-table";
import { JsonPreview } from "../../components/json-preview";
import { StatCard } from "../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../lib/api-client";
import type { MaintenanceStatus } from "../../lib/types";

async function loadMaintenanceStatus(): Promise<MaintenanceStatus | null> {
  try {
    return await damaApi.maintenanceStatus();
  } catch {
    return null;
  }
}

export default async function MaintenancePage() {
  const status = await loadMaintenanceStatus();

  if (!status) {
    return (
      <main className="page-shell">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Maintenance</p>
            <h1>Maintenance status unavailable</h1>
          </div>
          <p className="empty-state">
            Start the backend first, then refresh this page.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Maintenance</p>
        <h1>Local maintenance center</h1>
        <p className="lead">
          Inspect database state, export files, backup files, and safe maintenance endpoints.
        </p>

        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/maintenance/status`}>
            Raw Maintenance Status
          </a>
          <a href={`${DAMA_API_BASE_URL}/maintenance/database/backup`}>
            Backup Endpoint
          </a>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          label="Database"
          value={status.database.exists ? "Ready" : "Missing"}
          helper={`${status.database.size_bytes} bytes`}
        />
        <StatCard
          label="Exports"
          value={status.exports.file_count}
          helper={`${status.exports.total_size_bytes} bytes`}
        />
        <StatCard
          label="Backups"
          value={status.backups.file_count}
          helper={`${status.backups.total_size_bytes} bytes`}
        />
        <StatCard
          label="Maintenance"
          value={status.maintenance_ready ? "Ready" : "Pending"}
          helper="Local maintenance API"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Create Database Backup"
          description="Use the POST endpoint or DAMA autopilot backup command to create a local SQLite backup."
          href={`${DAMA_API_BASE_URL}/maintenance/database/backup`}
          label="POST endpoint"
        />
        <ActionCard
          title="Autopilot Backup"
          description="Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dama.ps1 backup"
          label="Local command"
        />
        <ActionCard
          title="Backend Check"
          description="Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dama.ps1 check"
          label="Local command"
        />
      </section>

      <section className="breakdown-grid two-card-grid">
        <CountBreakdown title="Database tables" items={status.database.tables} />
        <CountBreakdown
          title="Directory files"
          items={{
            exports: status.exports.file_count,
            backups: status.backups.file_count
          }}
        />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Backups</p>
            <h2>Recent backup files</h2>
          </div>

          <DataTable
            emptyLabel="No backup files found."
            items={status.backups.recent}
            columns={[
              {
                key: "file",
                label: "File",
                render: (item) => item.file_name
              },
              {
                key: "size",
                label: "Size",
                render: (item) => `${item.size_bytes} bytes`
              }
            ]}
          />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Exports</p>
            <h2>Recent export files</h2>
          </div>

          <DataTable
            emptyLabel="No export files found."
            items={status.exports.recent}
            columns={[
              {
                key: "file",
                label: "File",
                render: (item) => item.file_name
              },
              {
                key: "size",
                label: "Size",
                render: (item) => `${item.size_bytes} bytes`
              }
            ]}
          />
        </section>
      </section>

      <JsonPreview title="Maintenance payload" data={status} />
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
.action-card,
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
.readiness-grid,
.action-grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 24px;
}

.action-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 24px;
}

.stat-card,
.action-card {
  display: grid;
  gap: 8px;
  padding: 24px;
  border-radius: 22px;
  text-decoration: none;
}

.action-card span {
  color: var(--accent);
  font-weight: 900;
}

.action-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.action-card strong {
  width: fit-content;
  padding: 8px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
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
  .two-card-grid,
  .action-grid {
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
  .two-card-grid,
  .action-grid {
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
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
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
    ".\frontend\src\components\status-pill.tsx",
    ".\frontend\src\components\action-card.tsx",
    ".\frontend\src\components\json-preview.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$Nav = Get-Content ".\frontend\src\components\app-nav.tsx" -Raw
$WorkflowsPage = Get-Content ".\frontend\src\app\workflows\page.tsx" -Raw
$ExportsPage = Get-Content ".\frontend\src\app\exports\page.tsx" -Raw
$MaintenancePage = Get-Content ".\frontend\src\app\maintenance\page.tsx" -Raw

if ($ApiClient -notmatch "projectOutputPlan") {
    throw "API client does not expose projectOutputPlan."
}

if ($ApiClient -notmatch "maintenanceStatus") {
    throw "API client does not expose maintenanceStatus."
}

if ($Nav -notmatch "/workflows") {
    throw "Navigation does not include workflows."
}

if ($Nav -notmatch "/exports") {
    throw "Navigation does not include exports."
}

if ($Nav -notmatch "/maintenance") {
    throw "Navigation does not include maintenance."
}

if ($WorkflowsPage -notmatch "damaApi.projects") {
    throw "Workflows page does not load projects."
}

if ($ExportsPage -notmatch "dashboardSummary") {
    throw "Exports page does not load dashboard summary."
}

if ($MaintenancePage -notmatch "maintenanceStatus") {
    throw "Maintenance page does not load maintenance status."
}

Write-Host "Frontend workflow/export/maintenance UI check passed."
    ''',
)


write_file(
    "docs/workflow-ui.md",
    r'''
# DAMA Workflow, Export, and Maintenance UI

Super Pack K adds frontend pages for workflow operations, exports, and maintenance.

## Added Routes

    /workflows
    /workflows/[projectId]
    /exports
    /maintenance

## Workflow UI

The workflow index page lists projects and links to project workflow pages.

The project workflow page shows:

- project metadata
- output plan
- draft asset endpoint link
- batch generation endpoint link
- export bundle endpoint link
- raw output plan JSON

## Export UI

The export page shows:

- Markdown export count
- recent local export files
- project bundle export endpoints

## Maintenance UI

The maintenance page shows:

- database status
- table row counts
- export file status
- backup file status
- backup endpoint
- autopilot backup command

## Safety Note

Interactive POST buttons are intentionally not implemented yet.

For now, risky operations are shown as API endpoints or local commands so the operator remains in control.
    ''',
)


append_once(
    "docs/frontend-routes.md",
    "## Super Pack K Routes",
    r'''
## Super Pack K Routes

Added routes:

    /workflows
    /workflows/[projectId]
    /exports
    /maintenance

Purpose:

Expose workflow planning, export status, and maintenance status in the frontend shell.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Super Pack K Completed",
    r'''
## Super Pack K Completed

Name:

Workflow UI + Export UI + Maintenance UI

Added files:

- frontend/src/components/action-card.tsx
- frontend/src/components/json-preview.tsx
- frontend/src/app/workflows/page.tsx
- frontend/src/app/workflows/[projectId]/page.tsx
- frontend/src/app/exports/page.tsx
- frontend/src/app/maintenance/page.tsx
- docs/workflow-ui.md

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- workflow project selection page
- project workflow output plan page
- export center page
- maintenance center page
- extended frontend API client
- extended navigation
- safer UI by linking POST operations instead of executing them directly

Purpose:

Move DAMA frontend into a broader operational dashboard that covers workflow, export, and maintenance surfaces.

Next recommended Super Pack:

Super Pack L: Frontend Build Hardening + TypeScript Validation

Suggested scope:

- add frontend install/build docs
- add optional npm build check when node_modules exists
- add TypeScript/Next compatibility fixes
- fix dynamic route typing if needed
- improve API client error display
    ''',
)

print("Super Pack K applied successfully.")
