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
