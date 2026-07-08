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
  BatchGenerateDryRunInput,
  BatchGenerateResponse,
  ContentAsset,
  CreateContentAssetInput,
  CreateProjectInput,
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

  createProject(input: CreateProjectInput): Promise<Project> {
    return requestJson<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(input)
    });
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

  createContentAsset(input: CreateContentAssetInput): Promise<ContentAsset> {
    return requestJson<ContentAsset>("/content-assets", {
      method: "POST",
      body: JSON.stringify(input)
    });
  }
};
    ''',
)


write_file(
    "frontend/src/components/form-status.tsx",
    r'''
type FormStatusProps = {
  type: "idle" | "success" | "error";
  message?: string;
};

export function FormStatus({ type, message }: FormStatusProps) {
  if (!message) {
    return null;
  }

  return <p className={`form-status form-status-${type}`}>{message}</p>;
}
    ''',
)


write_file(
    "frontend/src/components/create-project-form.tsx",
    r'''
"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import type { Project } from "../lib/types";
import { FormStatus } from "./form-status";

const defaultContentTypes = [
  "blog_post",
  "social_caption",
  "product_description"
];

export function CreateProjectForm() {
  const [name, setName] = useState("");
  const [projectType, setProjectType] = useState("content_campaign");
  const [language, setLanguage] = useState("en");
  const [description, setDescription] = useState("");
  const [contentTypes, setContentTypes] = useState(defaultContentTypes.join(", "));
  const [createdProject, setCreatedProject] = useState<Project | null>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });

    try {
      const project = await damaApi.createProject({
        name,
        project_type: projectType,
        language,
        description,
        content_types: contentTypes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      });

      setCreatedProject(project);
      setStatus({
        type: "success",
        message: "Project created successfully."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Project creation failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <label>
        Project name
        <input
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="DAMA Launch Campaign"
        />
      </label>

      <label>
        Project type
        <select
          value={projectType}
          onChange={(event) => setProjectType(event.target.value)}
        >
          <option value="content_campaign">content_campaign</option>
          <option value="product_launch">product_launch</option>
          <option value="video_package">video_package</option>
        </select>
      </label>

      <label>
        Language
        <input
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          placeholder="en"
        />
      </label>

      <label>
        Content types
        <input
          value={contentTypes}
          onChange={(event) => setContentTypes(event.target.value)}
          placeholder="blog_post, social_caption"
        />
      </label>

      <label>
        Description
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Short project description"
        />
      </label>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create project"}
      </button>

      <FormStatus type={status.type} message={status.message} />

      {createdProject ? (
        <a className="form-result-link" href={`/projects/${createdProject.id}`}>
          Open created project
        </a>
      ) : null}
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/components/create-content-asset-form.tsx",
    r'''
"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import type { ContentAsset, Project } from "../lib/types";
import { FormStatus } from "./form-status";

type CreateContentAssetFormProps = {
  projects: Project[];
};

export function CreateContentAssetForm({ projects }: CreateContentAssetFormProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [contentType, setContentType] = useState("blog_post");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [statusValue, setStatusValue] = useState("draft");
  const [createdAsset, setCreatedAsset] = useState<ContentAsset | null>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });

    try {
      const asset = await damaApi.createContentAsset({
        project_id: projectId,
        content_type: contentType,
        title,
        body,
        status: statusValue,
        source: "manual",
        metadata: {
          created_from: "frontend_shell"
        }
      });

      setCreatedAsset(asset);
      setStatus({
        type: "success",
        message: "Content asset created successfully."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Content asset creation failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <label>
        Project
        <select
          required
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        Content type
        <input
          required
          value={contentType}
          onChange={(event) => setContentType(event.target.value)}
          placeholder="blog_post"
        />
      </label>

      <label>
        Title
        <input
          required
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Content title"
        />
      </label>

      <label>
        Status
        <select
          value={statusValue}
          onChange={(event) => setStatusValue(event.target.value)}
        >
          <option value="draft">draft</option>
          <option value="review">review</option>
          <option value="approved">approved</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
      </label>

      <label>
        Body
        <textarea
          required
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Write content body..."
        />
      </label>

      <button type="submit" disabled={isSubmitting || projects.length === 0}>
        {isSubmitting ? "Creating..." : "Create content asset"}
      </button>

      <FormStatus
        type={projects.length === 0 ? "error" : status.type}
        message={
          projects.length === 0
            ? "Create a project first."
            : status.message
        }
      />

      {createdAsset ? (
        <a className="form-result-link" href={`/projects/${createdAsset.project_id}`}>
          Open asset project
        </a>
      ) : null}
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/components/workflow-dry-run-form.tsx",
    r'''
"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import type { BatchGenerateResponse } from "../lib/types";
import { FormStatus } from "./form-status";

type WorkflowDryRunFormProps = {
  projectId: string;
};

export function WorkflowDryRunForm({ projectId }: WorkflowDryRunFormProps) {
  const [model, setModel] = useState("qwen2.5-coder:7b");
  const [topic, setTopic] = useState("");
  const [contentTypes, setContentTypes] = useState("");
  const [maxOutputs, setMaxOutputs] = useState("2");
  const [result, setResult] = useState<BatchGenerateResponse | null>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });

    try {
      const response = await damaApi.batchGenerateDryRun(projectId, {
        model,
        topic: topic || undefined,
        content_types: contentTypes
          ? contentTypes.split(",").map((item) => item.trim()).filter(Boolean)
          : undefined,
        max_outputs: Number(maxOutputs) || 1,
        dry_run: true
      });

      setResult(response);
      setStatus({
        type: "success",
        message: "Dry run completed successfully."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Dry run failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="form-grid">
      <form className="form-card" onSubmit={handleSubmit}>
        <label>
          Model
          <input
            required
            value={model}
            onChange={(event) => setModel(event.target.value)}
          />
        </label>

        <label>
          Topic
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Optional topic override"
          />
        </label>

        <label>
          Content types
          <input
            value={contentTypes}
            onChange={(event) => setContentTypes(event.target.value)}
            placeholder="Optional: blog_post, social_caption"
          />
        </label>

        <label>
          Max outputs
          <input
            min="1"
            max="10"
            type="number"
            value={maxOutputs}
            onChange={(event) => setMaxOutputs(event.target.value)}
          />
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Running..." : "Run dry run"}
        </button>

        <FormStatus type={status.type} message={status.message} />
      </form>

      <section className="panel form-result-panel">
        <div className="panel-heading">
          <p className="eyebrow">Dry Run Result</p>
          <h2>Planned outputs</h2>
        </div>

        {result ? (
          <pre className="code-block">{JSON.stringify(result, null, 2)}</pre>
        ) : (
          <p className="empty-state">
            Run a dry run to preview planned outputs before generation.
          </p>
        )}
      </section>
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/app/projects/new/page.tsx",
    r'''
import { CreateProjectForm } from "../../../components/create-project-form";
import { PageHeader } from "../../../components/page-header";

export default function NewProjectPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Projects"
        title="Create project"
        lead="Create a safe new DAMA project record for content workflows."
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">New Project</p>
          <h2>Project details</h2>
        </div>

        <CreateProjectForm />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/content-assets/new/page.tsx",
    r'''
import { CreateContentAssetForm } from "../../../components/create-content-asset-form";
import { PageHeader } from "../../../components/page-header";
import { damaApi } from "../../../lib/api-client";
import type { Project } from "../../../lib/types";

async function loadProjects(): Promise<Project[]> {
  try {
    return await damaApi.projects();
  } catch {
    return [];
  }
}

export default async function NewContentAssetPage() {
  const projects = await loadProjects();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Content Assets"
        title="Create content asset"
        lead="Create a manual content asset connected to an existing project."
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">New Asset</p>
          <h2>Content details</h2>
        </div>

        <CreateContentAssetForm projects={projects} />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/workflows/[projectId]/dry-run/page.tsx",
    r'''
import { PageHeader } from "../../../../components/page-header";
import { WorkflowDryRunForm } from "../../../../components/workflow-dry-run-form";
import { damaApi } from "../../../../lib/api-client";
import type { Project } from "../../../../lib/types";

type WorkflowDryRunPageProps = {
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

export default async function WorkflowDryRunPage({ params }: WorkflowDryRunPageProps) {
  const project = await loadProject(params.projectId);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Workflow Dry Run"
        title={project ? project.name : "Workflow dry run"}
        lead="Preview planned batch generation outputs without creating content assets."
      />

      <WorkflowDryRunForm projectId={params.projectId} />
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/projects/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../components/data-table";
import { PageHeader } from "../../components/page-header";
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
      <PageHeader
        eyebrow="Projects"
        title="Project workspace"
        lead="Browse DAMA projects and open project summaries for content workflow management."
      >
        <div className="actions">
          <a href="/projects/new">Create project</a>
        </div>
      </PageHeader>

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
    "frontend/src/app/content-assets/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../components/data-table";
import { PageHeader } from "../../components/page-header";
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
      <PageHeader
        eyebrow="Content Assets"
        title="Content asset library"
        lead="Browse manual and AI-generated content assets stored inside DAMA."
      >
        <div className="actions">
          <a href="/content-assets/new">Create content asset</a>
        </div>
      </PageHeader>

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
    "frontend/src/app/workflows/[projectId]/page.tsx",
    r'''
import { ActionCard } from "../../../components/action-card";
import { DataTable, StatusPill } from "../../../components/data-table";
import { JsonPreview } from "../../../components/json-preview";
import { PageHeader } from "../../../components/page-header";
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
      <PageHeader
        eyebrow="Project Workflow"
        title={project.name}
        lead="Output planning and safe workflow operations for this project."
      >
        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/workflows/projects/${project.id}/output-plan`}>
            Raw Output Plan
          </a>
          <a href={`/workflows/${project.id}/dry-run`}>
            Dry Run UI
          </a>
          <a href={`${DAMA_API_BASE_URL}/projects/${project.id}/summary`}>
            Project Summary
          </a>
        </div>
      </PageHeader>

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
          title="Batch Dry Run UI"
          description="Preview planned outputs without generating or saving content."
          href={`/workflows/${project.id}/dry-run`}
          label="Open UI"
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
  --danger: #a84236;
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

button,
input,
select,
textarea {
  font: inherit;
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
.page-heading,
.form-card {
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

.actions a,
.form-result-link {
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
.action-grid,
.form-grid {
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

.form-grid {
  grid-template-columns: 420px 1fr;
  align-items: start;
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

.form-card {
  display: grid;
  gap: 16px;
  margin-top: 20px;
  padding: 24px;
  border-radius: 22px;
}

.form-card label {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-weight: 800;
}

.form-card input,
.form-card select,
.form-card textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: white;
  color: var(--text);
}

.form-card textarea {
  min-height: 140px;
  resize: vertical;
}

.form-card button {
  width: fit-content;
  padding: 12px 16px;
  border: 0;
  border-radius: 999px;
  background: var(--accent);
  color: white;
  font-weight: 900;
  cursor: pointer;
}

.form-card button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.form-status {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  font-weight: 800;
}

.form-status-success {
  background: rgba(79, 125, 73, 0.12);
  color: var(--success);
}

.form-status-error {
  background: rgba(168, 66, 54, 0.12);
  color: var(--danger);
}

.form-status-idle {
  display: none;
}

.form-result-panel {
  margin-top: 20px;
}

@media (max-width: 980px) {
  .dashboard-hero,
  .two-column,
  .form-grid {
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
    ".\frontend\src\app\projects\new\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\content-assets\new\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\dry-run\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
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
$ProjectForm = Get-Content ".\frontend\src\components\create-project-form.tsx" -Raw
$AssetForm = Get-Content ".\frontend\src\components\create-content-asset-form.tsx" -Raw
$DryRunForm = Get-Content ".\frontend\src\components\workflow-dry-run-form.tsx" -Raw
$ProjectsPage = Get-Content ".\frontend\src\app\projects\page.tsx" -Raw
$AssetsPage = Get-Content ".\frontend\src\app\content-assets\page.tsx" -Raw

if ($ApiClient -notmatch "createProject") {
    throw "API client does not expose createProject."
}

if ($ApiClient -notmatch "createContentAsset") {
    throw "API client does not expose createContentAsset."
}

if ($ApiClient -notmatch "batchGenerateDryRun") {
    throw "API client does not expose batchGenerateDryRun."
}

if ($ProjectForm -notmatch '"use client"') {
    throw "CreateProjectForm is not a client component."
}

if ($AssetForm -notmatch '"use client"') {
    throw "CreateContentAssetForm is not a client component."
}

if ($DryRunForm -notmatch '"use client"') {
    throw "WorkflowDryRunForm is not a client component."
}

if ($ProjectsPage -notmatch "/projects/new") {
    throw "Projects page does not link to create project page."
}

if ($AssetsPage -notmatch "/content-assets/new") {
    throw "Content assets page does not link to create asset page."
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

Write-Host "Frontend write UI shell check passed."
    ''',
)


write_file(
    "docs/frontend-write-ui.md",
    r'''
# DAMA Frontend Write UI Shells

Super Pack M adds safe write UI shells.

## Added Routes

    /projects/new
    /content-assets/new
    /workflows/[projectId]/dry-run

## Added Client Components

- CreateProjectForm
- CreateContentAssetForm
- WorkflowDryRunForm
- FormStatus

## Supported Safe Writes

## Create Project

Creates a new project through:

    POST /projects

## Create Content Asset

Creates a manual content asset through:

    POST /content-assets

## Workflow Dry Run

Runs safe batch planning only:

    POST /workflows/projects/{project_id}/batch-generate

With:

    dry_run = true

## Safety Rule

This pack does not add destructive actions.

It does not add delete buttons.

It does not add real batch generation execution from UI.

The workflow dry-run form always sends dry_run true.
    ''',
)


append_once(
    "docs/frontend-routes.md",
    "## Super Pack M Routes",
    r'''
## Super Pack M Routes

Added routes:

    /projects/new
    /content-assets/new
    /workflows/[projectId]/dry-run

Purpose:

Allow safe creation of projects, safe creation of manual content assets, and safe workflow dry-run previews.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Super Pack M Completed",
    r'''
## Super Pack M Completed

Name:

API Write UI Shells

Added files:

- frontend/src/components/form-status.tsx
- frontend/src/components/create-project-form.tsx
- frontend/src/components/create-content-asset-form.tsx
- frontend/src/components/workflow-dry-run-form.tsx
- frontend/src/app/projects/new/page.tsx
- frontend/src/app/content-assets/new/page.tsx
- frontend/src/app/workflows/[projectId]/dry-run/page.tsx
- docs/frontend-write-ui.md

Updated files:

- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/app/projects/page.tsx
- frontend/src/app/content-assets/page.tsx
- frontend/src/app/workflows/[projectId]/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- safe project creation UI
- safe manual content asset creation UI
- safe workflow dry-run UI
- API client write methods
- frontend form styles
- stronger frontend write UI checks

Purpose:

Move DAMA frontend from read-only dashboard to safe operator write workflows.

Next recommended Super Pack:

Super Pack N: Backend Pagination + Search + Frontend Filters

Suggested scope:

- query filters for projects and assets
- search by title/name
- status filters
- frontend filter UI
- safer list scaling
    ''',
)

print("Super Pack M applied successfully.")
