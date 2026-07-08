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
