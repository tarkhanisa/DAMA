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

export type CreateProjectInput = {
  name: string;
  project_type: string;
  language?: string;
  description?: string;
  content_types?: string[];
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

export type CreateContentAssetInput = {
  project_id: string;
  content_type: string;
  title: string;
  body: string;
  status?: string;
  source?: string;
  metadata?: Record<string, unknown>;
};

export type SearchResponse<T> = {
  total: number;
  limit: number;
  offset: number;
  items: T[];
};

export type ProjectSearchParams = {
  query?: string;
  status?: string;
  project_type?: string;
  language?: string;
  limit?: number;
  offset?: number;
};

export type ContentAssetSearchParams = {
  query?: string;
  project_id?: string;
  status?: string;
  content_type?: string;
  source?: string;
  limit?: number;
  offset?: number;
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

export type BatchGenerateDryRunInput = {
  model: string;
  topic?: string;
  content_types?: string[];
  max_outputs?: number;
  dry_run: true;
};

export type BatchGenerateResponse = {
  project_id: string;
  dry_run: boolean;
  planned_count: number;
  generated_count: number;
  planned_outputs: PlannedOutput[];
  saved_content_assets: ContentAsset[];
};

export type ExportResult = {
  export_type: string;
  file_name: string;
  file_path: string;
  title: string;
  created_at: string;
  content: string;
};

export type BackupResult = {
  backup_created: boolean;
  source_path: string;
  backup_path: string;
  size_bytes: number;
  created_at: string;
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
  BackupResult,
  BatchGenerateDryRunInput,
  BatchGenerateResponse,
  ContentAsset,
  ContentAssetSearchParams,
  CreateContentAssetInput,
  CreateProjectInput,
  DashboardSummary,
  ExportResult,
  FrontendContract,
  MaintenanceStatus,
  OutputPlanResponse,
  Project,
  ProjectContentAssetsResponse,
  ProjectSearchParams,
  ProjectSummary,
  SearchResponse
} from "./types";

export const DAMA_API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
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

function toQueryString(params: Record<string, string | number | undefined>): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && String(value).trim() !== "") {
      searchParams.set(key, String(value));
    }
  }

  const queryString = searchParams.toString();

  return queryString ? `?${queryString}` : "";
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

  backupDatabase(): Promise<BackupResult> {
    return requestJson<BackupResult>("/maintenance/database/backup", {
      method: "POST"
    });
  },

  async projects(): Promise<Project[]> {
    const data = await requestJson<unknown>("/projects");
    return normalizeListResponse<Project>(data, ["projects", "items", "results"]);
  },

  searchProjects(params: ProjectSearchParams): Promise<SearchResponse<Project>> {
    return requestJson<SearchResponse<Project>>(
      `/search/projects${toQueryString(params)}`
    );
  },

  createProject(input: CreateProjectInput): Promise<Project> {
    return requestJson<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },

  project(projectId: string): Promise<Project> {
    return requestJson<Project>(`/projects/${projectId}`);
  },

  updateProjectStatus(projectId: string, status: string): Promise<Project> {
    return requestJson<Project>(`/projects/${projectId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    });
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

  exportProjectBundle(projectId: string): Promise<ExportResult> {
    return requestJson<ExportResult>(`/exports/projects/${projectId}/bundle`, {
      method: "POST"
    });
  },

  batchGenerateDryRun(
    projectId: string,
    input: BatchGenerateDryRunInput
  ): Promise<BatchGenerateResponse> {
    return requestJson<BatchGenerateResponse>(
      `/workflows/projects/${projectId}/batch-generate`,
      {
        method: "POST",
        body: JSON.stringify(input)
      }
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
  },

  searchContentAssets(
    params: ContentAssetSearchParams
  ): Promise<SearchResponse<ContentAsset>> {
    return requestJson<SearchResponse<ContentAsset>>(
      `/search/content-assets${toQueryString(params)}`
    );
  },

  contentAsset(assetId: string): Promise<ContentAsset> {
    return requestJson<ContentAsset>(`/content-assets/${assetId}`);
  },

  createContentAsset(input: CreateContentAssetInput): Promise<ContentAsset> {
    return requestJson<ContentAsset>("/content-assets", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },

  updateContentAssetStatus(assetId: string, status: string): Promise<ContentAsset> {
    return requestJson<ContentAsset>(`/content-assets/${assetId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    });
  },

  exportContentAssetMarkdown(assetId: string): Promise<ExportResult> {
    return requestJson<ExportResult>(`/exports/content-assets/${assetId}/markdown`, {
      method: "POST"
    });
  }
};
    ''',
)


write_file(
    "frontend/src/components/operation-result.tsx",
    r'''
type OperationResultProps = {
  title: string;
  result: unknown;
};

export function OperationResult({ title, result }: OperationResultProps) {
  if (!result) {
    return null;
  }

  return (
    <section className="operation-result">
      <h3>{title}</h3>
      <pre className="code-block">{JSON.stringify(result, null, 2)}</pre>
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/safe-action-button.tsx",
    r'''
"use client";

import { useState } from "react";

import { FormStatus } from "./form-status";
import { OperationResult } from "./operation-result";

type SafeActionButtonProps = {
  label: string;
  confirmLabel: string;
  successMessage: string;
  action: () => Promise<unknown>;
};

export function SafeActionButton({
  label,
  confirmLabel,
  successMessage,
  action
}: SafeActionButtonProps) {
  const [isConfirming, setIsConfirming] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });

  async function runAction() {
    setIsRunning(true);
    setStatus({ type: "idle" });
    setResult(null);

    try {
      const response = await action();
      setResult(response);
      setStatus({
        type: "success",
        message: successMessage
      });
      setIsConfirming(false);
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Operation failed."
      });
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="safe-action">
      {!isConfirming ? (
        <button type="button" onClick={() => setIsConfirming(true)}>
          {label}
        </button>
      ) : (
        <div className="confirm-row">
          <button type="button" disabled={isRunning} onClick={runAction}>
            {isRunning ? "Running..." : confirmLabel}
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={isRunning}
            onClick={() => setIsConfirming(false)}
          >
            Cancel
          </button>
        </div>
      )}

      <FormStatus type={status.type} message={status.message} />
      <OperationResult title="Operation result" result={result} />
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/components/backup-action.tsx",
    r'''
"use client";

import { damaApi } from "../lib/api-client";
import { SafeActionButton } from "./safe-action-button";

export function BackupAction() {
  return (
    <SafeActionButton
      label="Create database backup"
      confirmLabel="Confirm backup"
      successMessage="Database backup created."
      action={() => damaApi.backupDatabase()}
    />
  );
}
    ''',
)


write_file(
    "frontend/src/components/export-project-action.tsx",
    r'''
"use client";

import { damaApi } from "../lib/api-client";
import { SafeActionButton } from "./safe-action-button";

type ExportProjectActionProps = {
  projectId: string;
};

export function ExportProjectAction({ projectId }: ExportProjectActionProps) {
  return (
    <SafeActionButton
      label="Export project bundle"
      confirmLabel="Confirm export"
      successMessage="Project bundle exported."
      action={() => damaApi.exportProjectBundle(projectId)}
    />
  );
}
    ''',
)


write_file(
    "frontend/src/components/export-content-asset-action.tsx",
    r'''
"use client";

import { damaApi } from "../lib/api-client";
import { SafeActionButton } from "./safe-action-button";

type ExportContentAssetActionProps = {
  assetId: string;
};

export function ExportContentAssetAction({ assetId }: ExportContentAssetActionProps) {
  return (
    <SafeActionButton
      label="Export asset markdown"
      confirmLabel="Confirm export"
      successMessage="Content asset exported."
      action={() => damaApi.exportContentAssetMarkdown(assetId)}
    />
  );
}
    ''',
)


write_file(
    "frontend/src/components/project-status-form.tsx",
    r'''
"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import { FormStatus } from "./form-status";
import { OperationResult } from "./operation-result";

type ProjectStatusFormProps = {
  projectId: string;
  currentStatus: string;
};

const projectStatuses = ["draft", "active", "review", "paused", "completed", "archived"];

export function ProjectStatusForm({ projectId, currentStatus }: ProjectStatusFormProps) {
  const [statusValue, setStatusValue] = useState(currentStatus);
  const [result, setResult] = useState<unknown>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });
    setResult(null);

    try {
      const response = await damaApi.updateProjectStatus(projectId, statusValue);
      setResult(response);
      setStatus({
        type: "success",
        message: "Project status updated."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Project status update failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card compact-form" onSubmit={handleSubmit}>
      <label>
        Project status
        <select
          value={statusValue}
          onChange={(event) => setStatusValue(event.target.value)}
        >
          {projectStatuses.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Updating..." : "Update project status"}
      </button>

      <FormStatus type={status.type} message={status.message} />
      <OperationResult title="Status update result" result={result} />
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/components/content-asset-status-form.tsx",
    r'''
"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import { FormStatus } from "./form-status";
import { OperationResult } from "./operation-result";

type ContentAssetStatusFormProps = {
  assetId: string;
  currentStatus: string;
};

const assetStatuses = ["draft", "review", "approved", "published", "archived"];

export function ContentAssetStatusForm({
  assetId,
  currentStatus
}: ContentAssetStatusFormProps) {
  const [statusValue, setStatusValue] = useState(currentStatus);
  const [result, setResult] = useState<unknown>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });
    setResult(null);

    try {
      const response = await damaApi.updateContentAssetStatus(assetId, statusValue);
      setResult(response);
      setStatus({
        type: "success",
        message: "Content asset status updated."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Content asset status update failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card compact-form" onSubmit={handleSubmit}>
      <label>
        Content asset status
        <select
          value={statusValue}
          onChange={(event) => setStatusValue(event.target.value)}
        >
          {assetStatuses.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Updating..." : "Update asset status"}
      </button>

      <FormStatus type={status.type} message={status.message} />
      <OperationResult title="Status update result" result={result} />
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/content-assets", label: "Content Assets" },
  { href: "/workflows", label: "Workflows" },
  { href: "/search", label: "Search" },
  { href: "/operations", label: "Operations" },
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
    "frontend/src/app/operations/page.tsx",
    r'''
import { BackupAction } from "../../components/backup-action";
import { DataTable, StatusPill } from "../../components/data-table";
import { ExportContentAssetAction } from "../../components/export-content-asset-action";
import { ExportProjectAction } from "../../components/export-project-action";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { damaApi } from "../../lib/api-client";
import type { ContentAsset, Project } from "../../lib/types";

async function loadProjects(): Promise<Project[]> {
  try {
    return await damaApi.projects();
  } catch {
    return [];
  }
}

async function loadContentAssets(): Promise<ContentAsset[]> {
  try {
    return await damaApi.contentAssets();
  } catch {
    return [];
  }
}

export default async function OperationsPage() {
  const [projects, assets] = await Promise.all([
    loadProjects(),
    loadContentAssets()
  ]);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Operations"
        title="Safe operational actions"
        lead="Run confirmation-first backup and export actions. No delete operations are available here."
      />

      <section className="stats-grid">
        <StatCard label="Projects" value={projects.length} helper="Available for bundle export" />
        <StatCard label="Assets" value={assets.length} helper="Available for markdown export" />
        <StatCard label="Backup" value="Safe" helper="Confirmation required" />
        <StatCard label="Delete" value="Disabled" helper="No destructive UI actions" />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Backup</p>
          <h2>Database backup</h2>
        </div>

        <BackupAction />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Projects</p>
          <h2>Project bundle exports</h2>
        </div>

        <DataTable<Project>
          emptyLabel="No projects found."
          items={projects.slice(0, 20)}
          columns={[
            {
              key: "name",
              label: "Project",
              render: (project) => (
                <a className="table-link" href={`/projects/${project.id}`}>
                  {project.name}
                </a>
              )
            },
            {
              key: "status",
              label: "Status",
              render: (project) => <StatusPill status={project.status} />
            },
            {
              key: "action",
              label: "Export",
              render: (project) => <ExportProjectAction projectId={project.id} />
            }
          ]}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Content</p>
          <h2>Content asset exports</h2>
        </div>

        <DataTable<ContentAsset>
          emptyLabel="No content assets found."
          items={assets.slice(0, 20)}
          columns={[
            {
              key: "title",
              label: "Asset",
              render: (asset) => (
                <a className="table-link" href={`/content-assets/${asset.id}`}>
                  {asset.title}
                </a>
              )
            },
            {
              key: "status",
              label: "Status",
              render: (asset) => <StatusPill status={asset.status} />
            },
            {
              key: "action",
              label: "Export",
              render: (asset) => <ExportContentAssetAction assetId={asset.id} />
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
import { ErrorPanel } from "../../../components/error-panel";
import { ExportProjectAction } from "../../../components/export-project-action";
import { PageHeader } from "../../../components/page-header";
import { ProjectStatusForm } from "../../../components/project-status-form";
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
        <ErrorPanel
          eyebrow="Project"
          title="Project not found"
          message="The selected project could not be loaded from the backend."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Project Detail"
        title={project.name}
        lead={project.description || "Project workflow and content asset overview."}
      >
        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/projects/${project.id}/summary`}>
            Raw Summary
          </a>
          <a href={`/workflows/${project.id}`}>
            Workflow
          </a>
          <a href={`/workflows/${project.id}/dry-run`}>
            Dry Run
          </a>
        </div>
      </PageHeader>

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

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Status</p>
            <h2>Update project status</h2>
          </div>

          <ProjectStatusForm projectId={project.id} currentStatus={project.status} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Export</p>
            <h2>Project bundle</h2>
          </div>

          <ExportProjectAction projectId={project.id} />
        </section>
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
    "frontend/src/app/content-assets/[assetId]/page.tsx",
    r'''
import { AssetBodyPreview } from "../../../components/asset-body-preview";
import { ContentAssetStatusForm } from "../../../components/content-asset-status-form";
import { ErrorPanel } from "../../../components/error-panel";
import { ExportContentAssetAction } from "../../../components/export-content-asset-action";
import { JsonPreview } from "../../../components/json-preview";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../../lib/api-client";
import type { ContentAsset } from "../../../lib/types";

type AssetDetailPageProps = {
  params: {
    assetId: string;
  } | Promise<{
    assetId: string;
  }>;
};

async function resolveParams(params: AssetDetailPageProps["params"]) {
  return await params;
}

async function loadAsset(assetId: string): Promise<ContentAsset | null> {
  try {
    return await damaApi.contentAsset(assetId);
  } catch {
    return null;
  }
}

export default async function AssetDetailPage({ params }: AssetDetailPageProps) {
  const resolvedParams = await resolveParams(params);
  const asset = await loadAsset(resolvedParams.assetId);

  if (!asset) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="Content Asset"
          title="Content asset not found"
          message="The selected content asset could not be loaded from the backend."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Content Asset"
        title={asset.title}
        lead="Inspect content asset metadata, body, project connection, and export endpoint."
      >
        <div className="actions">
          <a href={`/projects/${asset.project_id}`}>Open Project</a>
          <a href={`${DAMA_API_BASE_URL}/content-assets/${asset.id}`}>
            Raw Asset JSON
          </a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Status" value={asset.status} helper="Asset status" />
        <StatCard label="Source" value={asset.source} helper="Asset source" />
        <StatCard label="Type" value={asset.content_type} helper="Content type" />
        <StatCard label="Project" value="Linked" helper={asset.project_id} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Status</p>
            <h2>Update asset status</h2>
          </div>

          <ContentAssetStatusForm assetId={asset.id} currentStatus={asset.status} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Export</p>
            <h2>Markdown export</h2>
          </div>

          <ExportContentAssetAction assetId={asset.id} />
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Body</p>
          <h2>Content body</h2>
        </div>

        <AssetBodyPreview body={asset.body} />
      </section>

      <JsonPreview title="Asset metadata" data={asset.metadata ?? {}} />
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/maintenance/page.tsx",
    r'''
import { ActionCard } from "../../components/action-card";
import { BackupAction } from "../../components/backup-action";
import { CountBreakdown } from "../../components/count-breakdown";
import { DataTable } from "../../components/data-table";
import { ErrorPanel } from "../../components/error-panel";
import { JsonPreview } from "../../components/json-preview";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../lib/api-client";
import { formatBytes, formatNumber } from "../../lib/formatters";
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
        <ErrorPanel
          eyebrow="Maintenance"
          title="Maintenance status unavailable"
          message="Start the backend first, then refresh this page."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Maintenance"
        title="Local maintenance center"
        lead="Inspect database state, export files, backup files, and safe maintenance endpoints."
      >
        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/maintenance/status`}>
            Raw Maintenance Status
          </a>
          <a href="/operations">
            Operations
          </a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard
          label="Database"
          value={status.database.exists ? "Ready" : "Missing"}
          helper={formatBytes(status.database.size_bytes)}
        />
        <StatCard
          label="Exports"
          value={formatNumber(status.exports.file_count)}
          helper={formatBytes(status.exports.total_size_bytes)}
        />
        <StatCard
          label="Backups"
          value={formatNumber(status.backups.file_count)}
          helper={formatBytes(status.backups.total_size_bytes)}
        />
        <StatCard
          label="Maintenance"
          value={status.maintenance_ready ? "Ready" : "Pending"}
          helper="Local maintenance API"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Operations Center"
          description="Open the confirmation-first operations page."
          href="/operations"
          label="Open"
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

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Backup</p>
          <h2>Create database backup</h2>
        </div>

        <BackupAction />
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
                render: (item) => formatBytes(item.size_bytes)
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
                render: (item) => formatBytes(item.size_bytes)
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


append_once(
    "frontend/src/app/globals.css",
    "/* Release Pack O: safe operations */",
    r'''
/* Release Pack O: safe operations */

.safe-action {
  display: grid;
  gap: 12px;
  min-width: 220px;
}

.safe-action button,
.confirm-row button,
.secondary-button {
  width: fit-content;
  padding: 10px 14px;
  border: 0;
  border-radius: 999px;
  background: var(--accent);
  color: white;
  font-weight: 900;
  cursor: pointer;
}

.secondary-button {
  background: white !important;
  color: var(--accent) !important;
  border: 1px solid var(--border) !important;
}

.confirm-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.operation-result {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

.operation-result h3 {
  margin: 0;
  color: var(--accent);
  font-size: 15px;
}

.compact-form {
  margin-top: 0;
  box-shadow: none;
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
    ".\frontend\src\app\projects\new\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\content-assets\new\page.tsx",
    ".\frontend\src\app\content-assets\[assetId]\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\dry-run\page.tsx",
    ".\frontend\src\app\search\page.tsx",
    ".\frontend\src\app\search\projects\page.tsx",
    ".\frontend\src\app\search\content-assets\page.tsx",
    ".\frontend\src\app\operations\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\safe-action-button.tsx",
    ".\frontend\src\components\operation-result.tsx",
    ".\frontend\src\components\backup-action.tsx",
    ".\frontend\src\components\export-project-action.tsx",
    ".\frontend\src\components\export-content-asset-action.tsx",
    ".\frontend\src\components\project-status-form.tsx",
    ".\frontend\src\components\content-asset-status-form.tsx",
    ".\frontend\src\components\search-filter-card.tsx",
    ".\frontend\src\components\asset-body-preview.tsx",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx",
    ".\frontend\src\components\data-table.tsx",
    ".\frontend\src\components\status-pill.tsx",
    ".\frontend\src\components\action-card.tsx",
    ".\frontend\src\components\json-preview.tsx",
    ".\frontend\src\components\page-header.tsx",
    ".\frontend\src\components\error-panel.tsx",
    ".\frontend\src\components\form-status.tsx",
    ".\frontend\src\components\create-project-form.tsx",
    ".\frontend\src\components\create-content-asset-form.tsx",
    ".\frontend\src\components\workflow-dry-run-form.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$Nav = Get-Content ".\frontend\src\components\app-nav.tsx" -Raw
$SafeAction = Get-Content ".\frontend\src\components\safe-action-button.tsx" -Raw
$Operations = Get-Content ".\frontend\src\app\operations\page.tsx" -Raw
$ProjectDetail = Get-Content ".\frontend\src\app\projects\[projectId]\page.tsx" -Raw
$AssetDetail = Get-Content ".\frontend\src\app\content-assets\[assetId]\page.tsx" -Raw

if ($ApiClient -notmatch "backupDatabase") {
    throw "API client does not expose backupDatabase."
}

if ($ApiClient -notmatch "exportProjectBundle") {
    throw "API client does not expose exportProjectBundle."
}

if ($ApiClient -notmatch "exportContentAssetMarkdown") {
    throw "API client does not expose exportContentAssetMarkdown."
}

if ($ApiClient -notmatch "updateProjectStatus") {
    throw "API client does not expose updateProjectStatus."
}

if ($ApiClient -notmatch "updateContentAssetStatus") {
    throw "API client does not expose updateContentAssetStatus."
}

if ($Nav -notmatch "/operations") {
    throw "Navigation does not include operations."
}

if ($SafeAction -notmatch "Confirm") {
    throw "SafeActionButton does not include confirmation behavior."
}

if ($Operations -notmatch "BackupAction") {
    throw "Operations page does not include backup action."
}

if ($ProjectDetail -notmatch "ProjectStatusForm") {
    throw "Project detail page does not include status form."
}

if ($AssetDetail -notmatch "ContentAssetStatusForm") {
    throw "Content asset detail page does not include status form."
}

if (Test-Path ".\frontend\node_modules") {
    Write-Host "node_modules found. Running frontend typecheck..."
    Push-Location ".\frontend"
    try {
        npm run typecheck
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend typecheck failed."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "node_modules not found. Skipping npm typecheck."
}

Write-Host "Frontend safe operational actions check passed."
    ''',
)


write_file(
    "docs/safe-operations-ui.md",
    r'''
# DAMA Safe Operations UI

Release Pack O adds confirmation-first operational UI.

## Added Route

    /operations

## Added Safe Actions

- Create database backup
- Export project bundle
- Export content asset markdown
- Update project status
- Update content asset status

## Safety Rules

No delete operation is exposed.

No destructive operation is exposed.

Export and backup actions require confirmation.

Batch generation execution is still not exposed as a direct UI action.

## Added Client Components

- SafeActionButton
- OperationResult
- BackupAction
- ExportProjectAction
- ExportContentAssetAction
- ProjectStatusForm
- ContentAssetStatusForm
    ''',
)


append_once(
    "docs/frontend-routes.md",
    "## Release Pack O Routes",
    r'''
## Release Pack O Routes

Added route:

    /operations

Updated routes:

    /projects/[projectId]
    /content-assets/[assetId]
    /maintenance

Purpose:

Expose confirmation-first safe operations for backup, export, and status changes.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack O Completed",
    r'''
## Release Pack O Completed

Name:

Safe Operational Actions UI

Added frontend files:

- frontend/src/components/safe-action-button.tsx
- frontend/src/components/operation-result.tsx
- frontend/src/components/backup-action.tsx
- frontend/src/components/export-project-action.tsx
- frontend/src/components/export-content-asset-action.tsx
- frontend/src/components/project-status-form.tsx
- frontend/src/components/content-asset-status-form.tsx
- frontend/src/app/operations/page.tsx
- docs/safe-operations-ui.md

Updated files:

- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/components/app-nav.tsx
- frontend/src/app/projects/[projectId]/page.tsx
- frontend/src/app/content-assets/[assetId]/page.tsx
- frontend/src/app/maintenance/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- confirmation-first backup action
- confirmation-first project bundle export
- confirmation-first content asset markdown export
- project status update UI
- content asset status update UI
- operations center
- no delete operations

Next recommended Release Pack:

Release Pack P: Frontend Dependency Install + Real Typecheck Fixes

Suggested scope:

- run npm install
- run npm typecheck
- fix real TypeScript/Next errors
- run npm build if feasible
- add lockfile if generated
    ''',
)

print("Release Pack O applied successfully.")
