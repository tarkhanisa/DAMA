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
          <a href="/search/projects">Search projects</a>
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
