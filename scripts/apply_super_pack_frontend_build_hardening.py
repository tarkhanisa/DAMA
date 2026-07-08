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
    "frontend/src/lib/formatters.ts",
    r'''
export function formatNumber(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === "") {
    return "0";
  }

  const numberValue = typeof value === "number" ? value : Number(value);

  if (Number.isNaN(numberValue)) {
    return String(value);
  }

  return new Intl.NumberFormat("en").format(numberValue);
}

export function formatBytes(value: number | undefined | null): string {
  if (!value) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size = size / 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

export function fallback(value: string | undefined | null, empty = "—"): string {
  const normalized = String(value ?? "").trim();
  return normalized || empty;
}
    ''',
)


write_file(
    "frontend/src/components/page-header.tsx",
    r'''
type PageHeaderProps = {
  eyebrow: string;
  title: string;
  lead?: string;
  children?: React.ReactNode;
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
    "frontend/src/components/error-panel.tsx",
    r'''
type ErrorPanelProps = {
  eyebrow?: string;
  title: string;
  message: string;
  command?: string;
};

export function ErrorPanel({
  eyebrow = "Error",
  title,
  message,
  command
}: ErrorPanelProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      <p className="empty-state">{message}</p>
      {command ? <pre className="code-block">{command}</pre> : null}
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/data-table.tsx",
    r'''
import type { ReactNode } from "react";

import { StatusPill } from "./status-pill";

type Column<T> = {
  key: string;
  label: string;
  render: (item: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: Column<T>[];
  items: T[];
  emptyLabel: string;
};

export function DataTable<T,>({ columns, items, emptyLabel }: DataTableProps<T>) {
  if (items.length === 0) {
    return <p className="empty-state">{emptyLabel}</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key}>{column.render(item)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { StatusPill };
    ''',
)


write_file(
    "frontend/src/app/layout.tsx",
    r'''
import type { ReactNode } from "react";

import { AppNav } from "../components/app-nav";
import "./globals.css";

export const metadata = {
  title: "DAMA Dashboard",
  description: "AI Content Automation Platform dashboard"
};

export default function RootLayout({
  children
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppNav />
        {children}
      </body>
    </html>
  );
}
    ''',
)


write_file(
    "frontend/src/app/page.tsx",
    r'''
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
    ''',
)


write_file(
    "frontend/src/app/maintenance/page.tsx",
    r'''
import { ActionCard } from "../../components/action-card";
import { CountBreakdown } from "../../components/count-breakdown";
import { DataTable } from "../../components/data-table";
import { ErrorPanel } from "../../components/error-panel";
import { JsonPreview } from "../../components/json-preview";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../lib/api-client";
import { formatBytes, formatNumber } from "../../lib/formatters";
import type { MaintenanceStatus } from "../../lib/types";

async function loadMaintenanceStatus(): Promise<MaintenanceStatus | null> {
  try {
    return await damaApi.maintenanceStatus();
  } catch {
    return null;
  }
}

export default async function MaintenancePage() {
  const status = await loadMaintenanceStatus();

  if (!status) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="Maintenance"
          title="Maintenance status unavailable"
          message="Start the backend first, then refresh this page."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Maintenance"
        title="Local maintenance center"
        lead="Inspect database state, export files, backup files, and safe maintenance endpoints."
      >
        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/maintenance/status`}>
            Raw Maintenance Status
          </a>
          <a href={`${DAMA_API_BASE_URL}/maintenance/database/backup`}>
            Backup Endpoint
          </a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard
          label="Database"
          value={status.database.exists ? "Ready" : "Missing"}
          helper={formatBytes(status.database.size_bytes)}
        />
        <StatCard
          label="Exports"
          value={formatNumber(status.exports.file_count)}
          helper={formatBytes(status.exports.total_size_bytes)}
        />
        <StatCard
          label="Backups"
          value={formatNumber(status.backups.file_count)}
          helper={formatBytes(status.backups.total_size_bytes)}
        />
        <StatCard
          label="Maintenance"
          value={status.maintenance_ready ? "Ready" : "Pending"}
          helper="Local maintenance API"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Create Database Backup"
          description="Use the POST endpoint or DAMA autopilot backup command to create a local SQLite backup."
          href={`${DAMA_API_BASE_URL}/maintenance/database/backup`}
          label="POST endpoint"
        />
        <ActionCard
          title="Autopilot Backup"
          description="Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dama.ps1 backup"
          label="Local command"
        />
        <ActionCard
          title="Backend Check"
          description="Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dama.ps1 check"
          label="Local command"
        />
      </section>

      <section className="breakdown-grid two-card-grid">
        <CountBreakdown title="Database tables" items={status.database.tables} />
        <CountBreakdown
          title="Directory files"
          items={{
            exports: status.exports.file_count,
            backups: status.backups.file_count
          }}
        />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Backups</p>
            <h2>Recent backup files</h2>
          </div>

          <DataTable
            emptyLabel="No backup files found."
            items={status.backups.recent}
            columns={[
              {
                key: "file",
                label: "File",
                render: (item) => item.file_name
              },
              {
                key: "size",
                label: "Size",
                render: (item) => formatBytes(item.size_bytes)
              }
            ]}
          />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Exports</p>
            <h2>Recent export files</h2>
          </div>

          <DataTable
            emptyLabel="No export files found."
            items={status.exports.recent}
            columns={[
              {
                key: "file",
                label: "File",
                render: (item) => item.file_name
              },
              {
                key: "size",
                label: "Size",
                render: (item) => formatBytes(item.size_bytes)
              }
            ]}
          />
        </section>
      </section>

      <JsonPreview title="Maintenance payload" data={status} />
    </main>
  );
}
    ''',
)


write_file(
    "frontend/package.json",
    r'''
{
  "name": "dama-frontend",
  "version": "0.1.0",
  "private": true,
  "description": "Frontend foundation for DAMA AI Content Automation Platform.",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "check": "npm run typecheck"
  },
  "dependencies": {
    "next": "latest",
    "react": "latest",
    "react-dom": "latest"
  },
  "devDependencies": {
    "@types/node": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest",
    "typescript": "latest"
  }
}
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
    ".\frontend\src\app\projects\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx",
    ".\frontend\src\components\data-table.tsx",
    ".\frontend\src\components\status-pill.tsx",
    ".\frontend\src\components\action-card.tsx",
    ".\frontend\src\components\json-preview.tsx",
    ".\frontend\src\components\page-header.tsx",
    ".\frontend\src\components\error-panel.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$DataTable = Get-Content ".\frontend\src\components\data-table.tsx" -Raw
$Layout = Get-Content ".\frontend\src\app\layout.tsx" -Raw
$PackageJson = Get-Content ".\frontend\package.json" -Raw

if ($DataTable -notmatch "DataTable<T,>") {
    throw "DataTable generic syntax is not TSX-safe."
}

if ($Layout -notmatch "import type \{ ReactNode \}") {
    throw "Layout does not import ReactNode type."
}

if ($PackageJson -notmatch '"typecheck"') {
    throw "Frontend package.json does not include typecheck script."
}

if (Test-Path ".\frontend\node_modules") {
    Write-Host "node_modules found. Running frontend typecheck..."
    Push-Location ".\frontend"
    try {
        npm run typecheck
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend typecheck failed."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "node_modules not found. Skipping npm typecheck."
}

Write-Host "Frontend hardening check passed."
    ''',
)


write_file(
    "docs/frontend-build-hardening.md",
    r'''
# DAMA Frontend Build Hardening

Super Pack L prepares the frontend for real TypeScript and Next.js validation.

## Added

- formatter helpers
- shared PageHeader component
- shared ErrorPanel component
- TSX-safe generic DataTable
- ReactNode type import in layout
- frontend typecheck script
- optional npm typecheck in frontend-check

## Frontend Commands

Install dependencies:

    cd I:\DAMA\frontend
    npm install

Run typecheck:

    npm run typecheck

Run build:

    npm run build

## DAMA Autopilot Behavior

The DAMA frontend check always validates required files.

If frontend/node_modules exists, it also runs:

    npm run typecheck

If node_modules does not exist, it skips npm typecheck to keep backend-first development fast.
    ''',
)


append_once(
    "docs/frontend-foundation.md",
    "## Build Hardening",
    r'''
## Build Hardening

Super Pack L adds TypeScript build hardening:

- TSX-safe DataTable generic syntax
- ReactNode type import
- formatter helpers
- shared error and page header components
- package typecheck script
- optional frontend typecheck when node_modules exists
    ''',
)


append_once(
    "docs/project-status.md",
    "## Super Pack L Completed",
    r'''
## Super Pack L Completed

Name:

Frontend Build Hardening + TypeScript Validation

Added files:

- frontend/src/lib/formatters.ts
- frontend/src/components/page-header.tsx
- frontend/src/components/error-panel.tsx
- docs/frontend-build-hardening.md

Updated files:

- frontend/src/components/data-table.tsx
- frontend/src/app/layout.tsx
- frontend/src/app/page.tsx
- frontend/src/app/maintenance/page.tsx
- frontend/package.json
- scripts/frontend-check.ps1
- docs/frontend-foundation.md
- docs/project-status.md

Added behavior:

- TSX-safe generic table component
- shared error panel
- shared page header
- number and byte formatting helpers
- optional npm typecheck when node_modules exists
- stronger frontend hardening checks

Purpose:

Prepare DAMA frontend for real dependency installation, TypeScript validation, and Next.js build checks.

Next recommended Super Pack:

Super Pack M: API Write UI Shells

Suggested scope:

- safe project create form shell
- content asset create form shell
- workflow dry-run form shell
- no destructive actions
- client component split where needed
    ''',
)

print("Super Pack L applied successfully.")
