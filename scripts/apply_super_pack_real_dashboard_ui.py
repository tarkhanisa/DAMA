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
    "frontend/src/components/stat-card.tsx",
    r'''
type StatCardProps = {
  label: string;
  value: string | number;
  helper?: string;
};

export function StatCard({ label, value, helper }: StatCardProps) {
  return (
    <article className="stat-card">
      <p>{label}</p>
      <strong>{value}</strong>
      {helper ? <span>{helper}</span> : null}
    </article>
  );
}
    ''',
)


write_file(
    "frontend/src/components/readiness-panel.tsx",
    r'''
type ReadinessPanelProps = {
  readiness: {
    has_projects: boolean;
    has_content_assets: boolean;
    has_exports: boolean;
    dashboard_ready: boolean;
    workflow_ready: boolean;
    export_ready: boolean;
  };
};

const readinessLabels: Record<string, string> = {
  has_projects: "Projects exist",
  has_content_assets: "Content assets exist",
  has_exports: "Exports exist",
  dashboard_ready: "Dashboard ready",
  workflow_ready: "Workflow ready",
  export_ready: "Export ready"
};

export function ReadinessPanel({ readiness }: ReadinessPanelProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">Readiness</p>
        <h2>System readiness</h2>
      </div>

      <div className="readiness-grid">
        {Object.entries(readiness).map(([key, value]) => (
          <div key={key} className={value ? "readiness-item is-ready" : "readiness-item"}>
            <span>{value ? "Ready" : "Pending"}</span>
            <strong>{readinessLabels[key] ?? key}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/recent-list.tsx",
    r'''
type RecentItem = {
  id?: string;
  name?: string;
  title?: string;
  project_type?: string;
  content_type?: string;
  status?: string;
  source?: string;
  created_at?: string;
};

type RecentListProps = {
  title: string;
  eyebrow: string;
  emptyLabel: string;
  items: RecentItem[];
};

export function RecentList({ title, eyebrow, emptyLabel, items }: RecentListProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>

      {items.length === 0 ? (
        <p className="empty-state">{emptyLabel}</p>
      ) : (
        <div className="recent-list">
          {items.map((item, index) => (
            <article key={item.id ?? index} className="recent-item">
              <div>
                <h3>{item.name ?? item.title ?? "Untitled"}</h3>
                <p>
                  {item.project_type ?? item.content_type ?? "item"}
                  {item.source ? ` · ${item.source}` : ""}
                </p>
              </div>
              <span>{item.status ?? "unknown"}</span>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/count-breakdown.tsx",
    r'''
type CountBreakdownProps = {
  title: string;
  items: Record<string, number>;
};

export function CountBreakdown({ title, items }: CountBreakdownProps) {
  const entries = Object.entries(items);

  return (
    <article className="breakdown-card">
      <h3>{title}</h3>

      {entries.length === 0 ? (
        <p>No data yet.</p>
      ) : (
        <ul>
          {entries.map(([key, value]) => (
            <li key={key}>
              <span>{key}</span>
              <strong>{value}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
    ''',
)


write_file(
    "frontend/src/components/link-card.tsx",
    r'''
type LinkCardProps = {
  title: string;
  description: string;
  href: string;
};

export function LinkCard({ title, description, href }: LinkCardProps) {
  return (
    <a className="link-card" href={href}>
      <span>{title}</span>
      <p>{description}</p>
    </a>
  );
}
    ''',
)


write_file(
    "frontend/src/app/page.tsx",
    r'''
import { CountBreakdown } from "../components/count-breakdown";
import { LinkCard } from "../components/link-card";
import { ReadinessPanel } from "../components/readiness-panel";
import { RecentList } from "../components/recent-list";
import { StatCard } from "../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../lib/api-client";
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
              value={summary.projects.total}
              helper="Total stored projects"
            />
            <StatCard
              label="Content Assets"
              value={summary.content_assets.total}
              helper="Manual and AI-generated assets"
            />
            <StatCard
              label="Markdown Exports"
              value={summary.exports.total_markdown_files}
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
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Backend</p>
            <h2>Backend is not reachable</h2>
          </div>
          <p className="empty-state">
            Start the backend first, then refresh this page.
          </p>
          <pre className="code-block">cd I:\DAMA\backend{"\n"}.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload</pre>
        </section>
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

.page-shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 72px;
}

.hero,
.panel,
.stat-card,
.breakdown-card,
.link-card {
  border: 1px solid var(--border);
  background: rgba(255, 250, 242, 0.88);
  box-shadow: 0 24px 80px rgba(47, 42, 36, 0.06);
  backdrop-filter: blur(8px);
}

.hero {
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

.stats-grid,
.breakdown-grid,
.link-grid,
.readiness-grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 24px;
}

.stat-card {
  display: grid;
  gap: 8px;
  padding: 24px;
  border-radius: 22px;
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

.readiness-item strong {
  font-size: 16px;
}

.breakdown-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 24px;
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

.recent-item span {
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

@media (max-width: 980px) {
  .dashboard-hero,
  .two-column {
    grid-template-columns: 1fr;
  }

  .stats-grid,
  .breakdown-grid,
  .link-grid,
  .readiness-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .hero,
  .panel {
    padding: 24px;
  }

  .stats-grid,
  .breakdown-grid,
  .link-grid,
  .readiness-grid {
    grid-template-columns: 1fr;
  }
}
    ''',
)


write_file(
    "docs/dashboard-ui.md",
    r'''
# DAMA Dashboard UI

Super Pack I adds the first real dashboard UI.

## Current Data Source

The dashboard page fetches:

    GET /dashboard/summary
    GET /developer/frontend-contract

## Current UI Sections

- Hero status
- Project count
- Content asset count
- Markdown export count
- Workflow readiness
- System readiness panel
- Project breakdowns
- Content asset breakdowns
- Recent projects
- Recent content assets
- Developer quick links

## Backend Requirement

Start backend first:

    cd I:\DAMA\backend
    .\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

## Frontend Requirement

Install dependencies:

    cd I:\DAMA\frontend
    npm install

Run frontend:

    npm run dev

## Notes

The dashboard page is resilient. If the backend is unavailable, it shows a backend unavailable state instead of crashing.
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
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        throw "Frontend foundation file is missing: $File"
    }
}

$DashboardPage = Get-Content ".\frontend\src\app\page.tsx" -Raw

if ($DashboardPage -notmatch "dashboardSummary") {
    throw "Dashboard page does not use dashboardSummary API client."
}

if ($DashboardPage -notmatch "ReadinessPanel") {
    throw "Dashboard page does not render ReadinessPanel."
}

Write-Host "Frontend dashboard check passed."
    ''',
)


append_once(
    "docs/frontend-foundation.md",
    "## Real Dashboard UI",
    r'''
## Real Dashboard UI

Super Pack I upgraded the frontend from a placeholder landing page to a real dashboard UI.

Added components:

- StatCard
- ReadinessPanel
- RecentList
- CountBreakdown
- LinkCard

The page now fetches dashboard data from the backend and displays operational summaries.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Super Pack I Completed",
    r'''
## Super Pack I Completed

Name:

Real Dashboard UI

Added files:

- frontend/src/components/stat-card.tsx
- frontend/src/components/readiness-panel.tsx
- frontend/src/components/recent-list.tsx
- frontend/src/components/count-breakdown.tsx
- frontend/src/components/link-card.tsx
- docs/dashboard-ui.md

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-foundation.md
- docs/project-status.md

Added behavior:

- dashboard data fetching
- backend unavailable fallback
- readiness UI
- summary stat cards
- recent project list
- recent content asset list
- developer quick links

Purpose:

Move DAMA frontend from static foundation to real dashboard UI backed by API data.

Next recommended Super Pack:

Super Pack J: Projects UI + Content Assets UI

Suggested scope:

- project list page
- project detail page shell
- content asset list page
- API client extensions
- frontend route map docs
    ''',
)

print("Super Pack I applied successfully.")
