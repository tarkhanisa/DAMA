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
