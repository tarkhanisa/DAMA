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
