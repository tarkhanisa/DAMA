import { CountBreakdown } from "../components/count-breakdown";
import { ErrorPanel } from "../components/error-panel";
import { LinkCard } from "../components/link-card";
import { ReadinessPanel } from "../components/readiness-panel";
import { RecentList } from "../components/recent-list";
import { StatCard } from "../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../lib/api-client";
import { formatNumber } from "../lib/formatters";
import type { DashboardSummary, FrontendContract } from "../lib/types";

async function loadDashboardSummary(): Promise<DashboardSummary | null> {
  try {
    return await damaApi.dashboardSummary();
  } catch {
    return null;
  }
}

async function loadFrontendContract(): Promise<FrontendContract | null> {
  try {
    return await damaApi.frontendContract();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const [summary, contract] = await Promise.all([
    loadDashboardSummary(),
    loadFrontendContract()
  ]);

  return (
    <main className="page-shell">
      <section className="hero dashboard-hero">
        <div>
          <p className="eyebrow">DAMA Dashboard</p>
          <h1>AI Content Automation Platform</h1>
          <p className="lead">
            Project workflow, content assets, exports, maintenance, and developer readiness in one local dashboard.
          </p>
        </div>

        <div className="hero-status">
          <span>{summary ? "Backend connected" : "Backend unavailable"}</span>
          <strong>{contract?.endpoint_count ?? "—"}</strong>
          <p>registered endpoints</p>
        </div>
      </section>

      {summary ? (
        <>
          <section className="stats-grid">
            <StatCard
              label="Projects"
              value={formatNumber(summary.projects.total)}
              helper="Total stored projects"
            />
            <StatCard
              label="Content Assets"
              value={formatNumber(summary.content_assets.total)}
              helper="Manual and AI-generated assets"
            />
            <StatCard
              label="Markdown Exports"
              value={formatNumber(summary.exports.total_markdown_files)}
              helper="Local export files"
            />
            <StatCard
              label="Workflow"
              value={summary.readiness.workflow_ready ? "Ready" : "Pending"}
              helper="Project + content readiness"
            />
          </section>

          <ReadinessPanel readiness={summary.readiness} />

          <section className="breakdown-grid">
            <CountBreakdown title="Projects by status" items={summary.projects.by_status} />
            <CountBreakdown title="Projects by type" items={summary.projects.by_type} />
            <CountBreakdown title="Assets by status" items={summary.content_assets.by_status} />
            <CountBreakdown title="Assets by source" items={summary.content_assets.by_source} />
          </section>

          <section className="two-column">
            <RecentList
              eyebrow="Projects"
              title="Recent projects"
              emptyLabel="No projects yet."
              items={summary.projects.recent}
            />
            <RecentList
              eyebrow="Content"
              title="Recent content assets"
              emptyLabel="No content assets yet."
              items={summary.content_assets.recent}
            />
          </section>
        </>
      ) : (
        <ErrorPanel
          eyebrow="Backend"
          title="Backend is not reachable"
          message="Start the backend first, then refresh this page."
          command={"cd I:\\DAMA\\backend\n.\\.venv\\Scripts\\python.exe -m uvicorn src.main:app --reload"}
        />
      )}

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Developer</p>
          <h2>Quick links</h2>
        </div>

        <div className="link-grid">
          <LinkCard
            title="API Docs"
            description="Open FastAPI Swagger UI."
            href={`${DAMA_API_BASE_URL}/docs`}
          />
          <LinkCard
            title="Dashboard Summary"
            description="Inspect raw dashboard summary JSON."
            href={`${DAMA_API_BASE_URL}/dashboard/summary`}
          />
          <LinkCard
            title="Frontend Contract"
            description="Inspect frontend contract JSON."
            href={`${DAMA_API_BASE_URL}/developer/frontend-contract`}
          />
          <LinkCard
            title="Endpoint Map"
            description="Inspect all backend endpoints."
            href={`${DAMA_API_BASE_URL}/developer/endpoint-map`}
          />
        </div>
      </section>
    </main>
  );
}
