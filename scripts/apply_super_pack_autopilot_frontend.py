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
    "scripts/dama.ps1",
    r'''
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("check", "status", "ship", "backup", "help")]
    [string] $Command,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Rest
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Message = ($Rest -join " ").Trim()

function Show-Help {
    Write-Host ""
    Write-Host "DAMA Autopilot Runner"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  check         Run backend and frontend readiness checks"
    Write-Host "  status        Show Git status and recent commits"
    Write-Host "  ship MESSAGE  Run checks, stage all changes, commit, and push"
    Write-Host "  backup        Create local database backup through backend service"
    Write-Host "  help          Show this help"
    Write-Host ""
}

switch ($Command) {
    "help" {
        Show-Help
    }

    "status" {
        Write-Host "Git status:"
        git status --short

        Write-Host ""
        Write-Host "Recent commits:"
        git log --oneline -8
    }

    "check" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\dama-check.ps1"
    }

    "ship" {
        if (-not $Message) {
            throw "Commit message is required."
        }

        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\dama-ship.ps1" -Message $Message
    }

    "backup" {
        Push-Location ".\backend"
        try {
            & ".\.venv\Scripts\python.exe" -c "from fastapi.testclient import TestClient; from src.main import app; client=TestClient(app); r=client.post('/maintenance/database/backup'); print(r.status_code); print(r.json())"
        }
        finally {
            Pop-Location
        }
    }
}
    ''',
)


write_file(
    "scripts/dama-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "DAMA check started."

Write-Host ""
Write-Host "Checking backend..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\backend-check.ps1"

Write-Host ""
Write-Host "Checking frontend foundation..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\frontend-check.ps1"

Write-Host ""
Write-Host "DAMA check completed."
    ''',
)


write_file(
    "scripts/dama-ship.ps1",
    r'''
param(
    [Parameter(Mandatory = $true)]
    [string] $Message
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $Message.Trim()) {
    throw "Commit message cannot be empty."
}

Write-Host "DAMA ship started."

Write-Host ""
Write-Host "Running checks before shipping..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\dama-check.ps1"

Write-Host ""
Write-Host "Checking Git status..."
$Changes = git status --short

if (-not $Changes) {
    Write-Host "No changes to commit."
    exit 0
}

$Changes

Write-Host ""
Write-Host "Staging all changes..."
git add -A

if ($LASTEXITCODE -ne 0) {
    throw "git add failed."
}

Write-Host ""
Write-Host "Checking staged changes..."
git diff --cached --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes to commit."
    exit 0
}

Write-Host ""
Write-Host "Committing..."
git commit -m $Message

if ($LASTEXITCODE -ne 0) {
    throw "git commit failed."
}

Write-Host ""
Write-Host "Pushing..."
git push

if ($LASTEXITCODE -ne 0) {
    throw "git push failed."
}

Write-Host ""
Write-Host "DAMA ship completed."
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
    ".\frontend\src\lib\types.ts"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        throw "Frontend foundation file is missing: $File"
    }
}

Write-Host "Frontend foundation check passed."
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
    "check": "echo Frontend structure check is handled by scripts/frontend-check.ps1"
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
    "frontend/next.config.mjs",
    r'''
const nextConfig = {
  reactStrictMode: true
};

export default nextConfig;
    ''',
)


write_file(
    "frontend/tsconfig.json",
    r'''
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
    ''',
)


write_file(
    "frontend/README.md",
    r'''
# DAMA Frontend

This is the frontend foundation for DAMA.

Backend:

    http://127.0.0.1:8000

API docs:

    http://127.0.0.1:8000/docs

Frontend contract:

    GET /developer/frontend-contract

Dashboard summary:

    GET /dashboard/summary

## Planned Sections

- Dashboard
- Projects
- Content Assets
- Workflows
- Exports
- Maintenance
- Developer

## Local Development

Install dependencies:

    npm install

Run frontend:

    npm run dev
    ''',
)


write_file(
    "frontend/src/lib/types.ts",
    r'''
export type DamaError = {
  error: {
    type: "http_error" | "validation_error";
    status_code: number;
    message: string;
    path: string;
    details?: unknown[];
  };
};

export type DashboardSummary = {
  system: Record<string, unknown>;
  projects: {
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    recent: unknown[];
  };
  content_assets: {
    total: number;
    by_status: Record<string, number>;
    by_content_type: Record<string, number>;
    by_source: Record<string, number>;
    recent: unknown[];
  };
  exports: {
    total_markdown_files: number;
    export_root: string;
    recent: unknown[];
  };
  readiness: {
    has_projects: boolean;
    has_content_assets: boolean;
    has_exports: boolean;
    dashboard_ready: boolean;
    workflow_ready: boolean;
    export_ready: boolean;
  };
};

export type FrontendContract = {
  name: string;
  version: string;
  backend_base_url: string;
  interactive_docs: string;
  openapi_json: string;
  recommended_frontend_sections: Array<{
    key: string;
    title: string;
    primary_endpoints: string[];
  }>;
  endpoint_count: number;
};
    ''',
)


write_file(
    "frontend/src/lib/api-client.ts",
    r'''
import type { DashboardSummary, FrontendContract } from "./types";

export const DAMA_API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${DAMA_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(JSON.stringify(data));
  }

  return data as T;
}

export const damaApi = {
  dashboardSummary(): Promise<DashboardSummary> {
    return requestJson<DashboardSummary>("/dashboard/summary");
  },

  frontendContract(): Promise<FrontendContract> {
    return requestJson<FrontendContract>("/developer/frontend-contract");
  },

  endpointMap(): Promise<unknown> {
    return requestJson<unknown>("/developer/endpoint-map");
  },

  runbook(): Promise<unknown> {
    return requestJson<unknown>("/developer/runbook");
  }
};
    ''',
)


write_file(
    "frontend/src/app/layout.tsx",
    r'''
import "./globals.css";

export const metadata = {
  title: "DAMA Dashboard",
  description: "AI Content Automation Platform dashboard"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
    ''',
)


write_file(
    "frontend/src/app/page.tsx",
    r'''
import { DAMA_API_BASE_URL } from "../lib/api-client";

const sections = [
  "Dashboard",
  "Projects",
  "Content Assets",
  "Workflows",
  "Exports",
  "Maintenance",
  "Developer"
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">DAMA Frontend Foundation</p>
        <h1>AI Content Automation Platform</h1>
        <p className="lead">
          This is the first frontend foundation for DAMA. The backend is already
          API-first and dashboard-ready.
        </p>

        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/docs`}>Open API Docs</a>
          <a href={`${DAMA_API_BASE_URL}/dashboard/summary`}>
            Dashboard Summary
          </a>
          <a href={`${DAMA_API_BASE_URL}/developer/frontend-contract`}>
            Frontend Contract
          </a>
        </div>
      </section>

      <section className="grid">
        {sections.map((section) => (
          <article key={section} className="card">
            <h2>{section}</h2>
            <p>Ready for the next frontend implementation step.</p>
          </article>
        ))}
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
  --text: #2f2a24;
  --muted: #75695d;
  --border: #e4d8c9;
  --accent: #9a5b2f;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--background);
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
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
  padding: 64px 0;
}

.hero {
  padding: 48px;
  border: 1px solid var(--border);
  border-radius: 28px;
  background: var(--surface);
  box-shadow: 0 24px 80px rgba(47, 42, 36, 0.08);
}

.eyebrow {
  margin: 0 0 12px;
  color: var(--accent);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1 {
  max-width: 760px;
  margin: 0;
  font-size: clamp(40px, 7vw, 76px);
  line-height: 0.95;
}

.lead {
  max-width: 720px;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 20px;
  line-height: 1.7;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 32px;
}

.actions a {
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: white;
  text-decoration: none;
  font-weight: 700;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.card {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
}

.card h2 {
  margin: 0;
  font-size: 20px;
}

.card p {
  margin: 12px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

@media (max-width: 760px) {
  .hero {
    padding: 28px;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
    ''',
)


write_file(
    "docs/development-workflow.md",
    r'''
# DAMA Development Workflow

DAMA includes an internal autopilot runner for faster local development.

## Main Command

    cd I:\DAMA
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 <command>

## Commands

Check everything:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check

Show status:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 status

Ship changes:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"

Create database backup:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 backup

## Ship Behavior

The ship command:

1. Runs backend smoke tests.
2. Runs frontend foundation check.
3. Shows Git status.
4. Stages all changes.
5. Commits with the given message.
6. Pushes to GitHub.
    ''',
)


write_file(
    "docs/frontend-foundation.md",
    r'''
# DAMA Frontend Foundation

The first frontend foundation is intentionally simple.

## Current Frontend Path

    frontend/

## Current Structure

    frontend/package.json
    frontend/next.config.mjs
    frontend/tsconfig.json
    frontend/src/app/layout.tsx
    frontend/src/app/page.tsx
    frontend/src/app/globals.css
    frontend/src/lib/api-client.ts
    frontend/src/lib/types.ts

## Backend Contract

The frontend should use:

    GET /developer/frontend-contract
    GET /dashboard/summary
    GET /developer/endpoint-map
    GET /developer/runbook

## Frontend Sections

- Dashboard
- Projects
- Content Assets
- Workflows
- Exports
- Maintenance
- Developer
    ''',
)


append_once(
    ".gitignore",
    "frontend/node_modules/",
    r'''
frontend/node_modules/
frontend/.next/
frontend/out/
frontend/.env.local
    ''',
)


append_once(
    "README.md",
    "## DAMA Autopilot",
    r'''
## DAMA Autopilot

Check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check

Status:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 status

Ship:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"

Backup:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 backup
    ''',
)


append_once(
    "docs/project-status.md",
    "## Super Pack H Completed",
    r'''
## Super Pack H Completed

Name:

Autopilot Runner + Frontend Foundation

Added files:

- scripts/dama.ps1
- scripts/dama-check.ps1
- scripts/dama-ship.ps1
- scripts/frontend-check.ps1
- frontend/package.json
- frontend/next.config.mjs
- frontend/tsconfig.json
- frontend/README.md
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/app/layout.tsx
- frontend/src/app/page.tsx
- frontend/src/app/globals.css
- docs/development-workflow.md
- docs/frontend-foundation.md

Purpose:

Reduce repetitive manual development steps and prepare DAMA for faster frontend implementation.
    ''',
)


print("Super Pack H applied successfully.")
