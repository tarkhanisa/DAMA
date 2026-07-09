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


def patch_main() -> None:
    target = ROOT / "backend/src/main.py"
    text = target.read_text(encoding="utf-8")

    if "from fastapi.middleware.cors import CORSMiddleware" not in text:
        text = text.replace(
            "from fastapi import FastAPI",
            "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware",
        )

    if "app.add_middleware(CORSMiddleware" not in text:
        marker = "app = FastAPI("
        index = text.find(marker)
        if index == -1:
            raise RuntimeError("Could not find FastAPI app creation.")

        end_index = text.find("\n)", index)
        if end_index == -1:
            raise RuntimeError("Could not find FastAPI app creation end.")

        insert_at = end_index + 2
        cors_block = r'''

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
        text = text[:insert_at] + cors_block + text[insert_at:]

    target.write_text(text, encoding="utf-8")
    print("Patched backend/src/main.py with CORS middleware.")


patch_main()


write_file(
    "frontend/src/components/page-header.tsx",
    r'''
import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  lead?: string;
  children?: ReactNode;
};

export function PageHeader({ eyebrow, title, lead, children }: PageHeaderProps) {
  return (
    <section className="page-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {lead ? <p className="lead">{lead}</p> : null}
      {children}
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/search-filter-card.tsx",
    r'''
import type { ReactNode } from "react";

type SearchFilterCardProps = {
  title: string;
  children: ReactNode;
};

export function SearchFilterCard({ title, children }: SearchFilterCardProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">Search</p>
        <h2>{title}</h2>
      </div>

      <form className="filter-form" method="get">
        {children}
        <button type="submit">Apply filters</button>
      </form>
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/create-project-form.tsx",
    r'''
"use client";

import type { FormEvent } from "react";
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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

import type { FormEvent } from "react";
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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

import type { FormEvent } from "react";
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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
    "frontend/src/components/project-status-form.tsx",
    r'''
"use client";

import type { FormEvent } from "react";
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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

import type { FormEvent } from "react";
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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
  params: Promise<{
    projectId: string;
  }>;
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
  const { projectId } = await params;

  const [project, summary] = await Promise.all([
    loadProject(projectId),
    loadProjectSummary(projectId)
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
    "frontend/src/app/workflows/[projectId]/page.tsx",
    r'''
import { ActionCard } from "../../../components/action-card";
import { DataTable, StatusPill } from "../../../components/data-table";
import { ErrorPanel } from "../../../components/error-panel";
import { JsonPreview } from "../../../components/json-preview";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../../lib/api-client";
import type { OutputPlanResponse, PlannedOutput, Project } from "../../../lib/types";

type WorkflowProjectPageProps = {
  params: Promise<{
    projectId: string;
  }>;
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
  const { projectId } = await params;

  const [project, outputPlan] = await Promise.all([
    loadProject(projectId),
    loadOutputPlan(projectId)
  ]);

  if (!project) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="Workflow"
          title="Project not found"
          message="The selected workflow project could not be loaded."
        />
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
    "frontend/src/app/workflows/[projectId]/dry-run/page.tsx",
    r'''
import { PageHeader } from "../../../../components/page-header";
import { WorkflowDryRunForm } from "../../../../components/workflow-dry-run-form";
import { damaApi } from "../../../../lib/api-client";
import type { Project } from "../../../../lib/types";

type WorkflowDryRunPageProps = {
  params: Promise<{
    projectId: string;
  }>;
};

async function loadProject(projectId: string): Promise<Project | null> {
  try {
    return await damaApi.project(projectId);
  } catch {
    return null;
  }
}

export default async function WorkflowDryRunPage({ params }: WorkflowDryRunPageProps) {
  const { projectId } = await params;
  const project = await loadProject(projectId);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Workflow Dry Run"
        title={project ? project.name : "Workflow dry run"}
        lead="Preview planned batch generation outputs without creating content assets."
      />

      <WorkflowDryRunForm projectId={projectId} />
    </main>
  );
}
    ''',
)


write_file(
    "scripts/frontend-real-build.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $Root "frontend"

Set-Location $FrontendPath

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Install Node.js first."
}

Write-Host "Installing frontend dependencies..."
npm install
if ($LASTEXITCODE -ne 0) {
    throw "npm install failed."
}

Write-Host "Running frontend typecheck..."
npm run typecheck
if ($LASTEXITCODE -ne 0) {
    throw "Frontend typecheck failed."
}

Write-Host "Running frontend build..."
npm run build
if ($LASTEXITCODE -ne 0) {
    throw "Frontend build failed."
}

Write-Host "Frontend real build completed."
    ''',
)


append_once(
    "docs/frontend-build-hardening.md",
    "## Release Pack P Real Build",
    r'''
## Release Pack P Real Build

Release Pack P adds a real frontend build script:

    scripts/frontend-real-build.ps1

It runs:

    npm install
    npm run typecheck
    npm run build

It also adds backend CORS support for the local Next.js frontend:

    http://127.0.0.1:3000
    http://localhost:3000
    http://127.0.0.1:3001
    http://localhost:3001
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack P Completed",
    r'''
## Release Pack P Completed

Name:

Real Frontend Install + TypeScript Fix + Build Validation

Added files:

- scripts/frontend-real-build.ps1

Updated files:

- backend/src/main.py
- frontend/src/components/page-header.tsx
- frontend/src/components/search-filter-card.tsx
- frontend/src/components/create-project-form.tsx
- frontend/src/components/create-content-asset-form.tsx
- frontend/src/components/workflow-dry-run-form.tsx
- frontend/src/components/project-status-form.tsx
- frontend/src/components/content-asset-status-form.tsx
- frontend/src/app/projects/[projectId]/page.tsx
- frontend/src/app/workflows/[projectId]/page.tsx
- frontend/src/app/workflows/[projectId]/dry-run/page.tsx
- docs/frontend-build-hardening.md
- docs/project-status.md

Added behavior:

- local CORS support for frontend to backend API calls
- TSX-safe ReactNode imports
- FormEvent type imports for client components
- Next dynamic route params compatibility
- real frontend install/typecheck/build script

Purpose:

Move frontend validation from file-existence checks to real Next.js/TypeScript build validation.
    ''',
)

print("Release Pack P applied successfully.")
