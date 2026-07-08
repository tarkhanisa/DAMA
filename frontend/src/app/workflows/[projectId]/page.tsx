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
