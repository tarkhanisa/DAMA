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
