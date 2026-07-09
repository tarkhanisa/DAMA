from pathlib import Path
import json

ROOT = Path("I:/DAMA")


def read_text(path: str) -> str:
    target = ROOT / path
    return target.read_text(encoding="utf-8") if target.exists() else ""


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


# 1) .gitignore hygiene
gitignore_path = ROOT / ".gitignore"
gitignore = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

ignore_block = """
# Frontend build/cache
frontend/node_modules/
frontend/.next/
frontend/out/
frontend/.env.local
frontend/tsconfig.tsbuildinfo
frontend/*.tsbuildinfo
frontend/.turbo/

# DAMA local runtime
backend/data/
backend/exports/
backend/backups/
"""

for line in ignore_block.strip().splitlines():
    if line and line not in gitignore:
        gitignore += "\n" + line

gitignore_path.write_text(gitignore.strip() + "\n", encoding="utf-8")
print("Updated .gitignore")


# 2) Remove frontend tsbuildinfo cache file from working tree
cache_file = ROOT / "frontend/tsconfig.tsbuildinfo"
if cache_file.exists():
    cache_file.unlink()
    print("Removed frontend/tsconfig.tsbuildinfo from working tree")


# 3) tsconfig: avoid producing tsbuildinfo in normal typecheck
tsconfig_path = ROOT / "frontend/tsconfig.json"
tsconfig = json.loads(tsconfig_path.read_text(encoding="utf-8"))

tsconfig.setdefault("compilerOptions", {})
tsconfig["compilerOptions"]["incremental"] = False

include = tsconfig.get("include", [])
for item in [
    "next-env.d.ts",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.ts",
    "**/*.tsx",
]:
    if item not in include:
        include.append(item)

tsconfig["include"] = include
tsconfig["exclude"] = ["node_modules"]

tsconfig_path.write_text(
    json.dumps(tsconfig, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print("Updated frontend/tsconfig.json")


# 4) Dev scripts
write_file(
    "scripts/dev-backend.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $Root "backend"

Set-Location $BackendPath

$PythonPath = Join-Path $BackendPath ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    throw "Backend virtual environment was not found: $PythonPath"
}

Write-Host "Starting DAMA backend on http://127.0.0.1:8000"
& $PythonPath -m uvicorn src.main:app --reload
    ''',
)

write_file(
    "scripts/dev-frontend.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $Root "frontend"

Set-Location $FrontendPath

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd was not found. Install Node.js first."
}

if (-not (Test-Path ".\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm.cmd install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
}

Write-Host "Starting DAMA frontend on http://localhost:3000"
npm.cmd run dev
    ''',
)

write_file(
    "scripts/dev-all.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

$BackendScript = Join-Path $Root "scripts\dev-backend.ps1"
$FrontendScript = Join-Path $Root "scripts\dev-frontend.ps1"

if (-not (Test-Path $BackendScript)) {
    throw "Backend dev script not found."
}

if (-not (Test-Path $FrontendScript)) {
    throw "Frontend dev script not found."
}

Write-Host "Opening DAMA backend and frontend in separate PowerShell windows..."

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-NoExit",
    "-File",
    $BackendScript
)

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-NoExit",
    "-File",
    $FrontendScript
)

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "API Docs: http://127.0.0.1:8000/docs"
    ''',
)

write_file(
    "scripts/repo-hygiene-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ForbiddenTrackedPatterns = @(
    "frontend/tsconfig.tsbuildinfo",
    "frontend/.next/",
    "frontend/node_modules/",
    "backend/data/",
    "backend/exports/",
    "backend/backups/"
)

$TrackedFiles = git ls-files

foreach ($Pattern in $ForbiddenTrackedPatterns) {
    foreach ($File in $TrackedFiles) {
        if ($File -like "$Pattern*") {
            throw "Forbidden tracked runtime/cache file found: $File"
        }
    }
}

Write-Host "Repo hygiene check passed."
    ''',
)


# 5) Update frontend-check to include repo hygiene expectations
write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    return [string]::Join("`n", (Get-Content -LiteralPath $Path))
}

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RequiredFiles = @(
    ".\frontend\README.md",
    ".\frontend\package.json",
    ".\frontend\package-lock.json",
    ".\frontend\next.config.mjs",
    ".\frontend\tsconfig.json",
    ".\frontend\next-env.d.ts",
    ".\frontend\src\app\layout.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\projects\page.tsx",
    ".\frontend\src\app\projects\new\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\content-assets\new\page.tsx",
    ".\frontend\src\app\content-assets\[assetId]\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\dry-run\page.tsx",
    ".\frontend\src\app\search\page.tsx",
    ".\frontend\src\app\search\projects\page.tsx",
    ".\frontend\src\app\search\content-assets\page.tsx",
    ".\frontend\src\app\operations\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\safe-action-button.tsx",
    ".\frontend\src\components\operation-result.tsx",
    ".\frontend\src\components\backup-action.tsx",
    ".\frontend\src\components\export-project-action.tsx",
    ".\frontend\src\components\export-content-asset-action.tsx",
    ".\frontend\src\components\project-status-form.tsx",
    ".\frontend\src\components\content-asset-status-form.tsx",
    ".\frontend\src\components\search-filter-card.tsx",
    ".\frontend\src\components\asset-body-preview.tsx",
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
    ".\frontend\src\components\error-panel.tsx",
    ".\frontend\src\components\form-status.tsx",
    ".\frontend\src\components\create-project-form.tsx",
    ".\frontend\src\components\create-content-asset-form.tsx",
    ".\frontend\src\components\workflow-dry-run-form.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$GitIgnore = Read-TextFile ".\.gitignore"
$ApiClient = Read-TextFile ".\frontend\src\lib\api-client.ts"
$Nav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$SafeAction = Read-TextFile ".\frontend\src\components\safe-action-button.tsx"
$Operations = Read-TextFile ".\frontend\src\app\operations\page.tsx"
$ProjectDetail = Read-TextFile ".\frontend\src\app\projects\[projectId]\page.tsx"
$AssetDetail = Read-TextFile ".\frontend\src\app\content-assets\[assetId]\page.tsx"
$TsConfig = Read-TextFile ".\frontend\tsconfig.json"

if ($GitIgnore -notmatch "frontend/tsconfig.tsbuildinfo") {
    throw ".gitignore does not ignore frontend/tsconfig.tsbuildinfo."
}

if ($TsConfig -match '"incremental": true') {
    throw "frontend tsconfig should not use incremental true in this repo."
}

if ($ApiClient -notmatch "backupDatabase") {
    throw "API client does not expose backupDatabase."
}

if ($ApiClient -notmatch "searchProjects") {
    throw "API client does not expose searchProjects."
}

if ($ApiClient -notmatch "searchContentAssets") {
    throw "API client does not expose searchContentAssets."
}

if ($Nav -notmatch "/operations") {
    throw "Navigation does not include operations."
}

if ($SafeAction -notmatch "Confirm") {
    throw "SafeActionButton does not include confirmation behavior."
}

if ($Operations -notmatch "BackupAction") {
    throw "Operations page does not include backup action."
}

if ($ProjectDetail -notmatch "ProjectStatusForm") {
    throw "Project detail page does not include status form."
}

if ($AssetDetail -notmatch "ContentAssetStatusForm") {
    throw "Content asset detail page does not include status form."
}

if (Test-Path ".\frontend\node_modules") {
    Write-Host "node_modules found. Running frontend typecheck..."
    Push-Location ".\frontend"
    try {
        npm.cmd run typecheck
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

Write-Host "Frontend production readiness check passed."
    ''',
)


# 6) README and docs
append_once(
    "README.md",
    "## DAMA Local Development",
    r'''
## DAMA Local Development

Start backend:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1

Start frontend:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1

Start both in separate PowerShell windows:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-all.ps1

Backend:

    http://127.0.0.1:8000

Frontend:

    http://localhost:3000

API Docs:

    http://127.0.0.1:8000/docs

Run full ship checks and commit/push:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Your commit message"
    ''',
)

write_file(
    "docs/local-development.md",
    r'''
# DAMA Local Development

## Backend

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1

Backend URL:

    http://127.0.0.1:8000

API Docs:

    http://127.0.0.1:8000/docs

## Frontend

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1

Frontend URL:

    http://localhost:3000

## Start Both

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-all.ps1

This opens backend and frontend in separate PowerShell windows.

## Real Frontend Build

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend-real-build.ps1

## Ship

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"
    ''',
)

write_file(
    "docs/production-readiness.md",
    r'''
# DAMA Production Readiness

DAMA is not production-deployed yet, but the repository now has a stronger local production-readiness baseline.

## Ready

- FastAPI backend
- Local SQLite persistence
- Ollama provider abstraction
- Prompt rendering
- Content generation
- Project persistence
- Content asset persistence
- Workflow planning
- Batch generation dry-run
- Markdown exports
- Maintenance status and backup
- Dashboard API
- Developer API
- Search API
- Next.js frontend
- Real frontend typecheck
- Real frontend build
- Autopilot check/ship workflow

## Safe UI Available

- Create project
- Create content asset
- Search projects
- Search content assets
- View project detail
- View content asset detail
- Workflow dry-run
- Export project bundle
- Export content asset markdown
- Create database backup
- Update project status
- Update content asset status

## Not Exposed Intentionally

- Delete operations
- Destructive bulk operations
- Non-dry-run batch generation from UI
- Public deployment configuration
- Authentication/authorization
- Multi-user roles
- External database deployment
- Cloud storage
- Queue workers

## Before Real Production

Required later:

- Authentication
- Authorization
- Environment-based configuration
- Production database
- Migration system
- Secrets management
- Rate limiting
- Background queue
- Observability/logging
- Deployment scripts
- Security review
- Dependency audit plan
    ''',
)

write_file(
    "docs/repo-hygiene.md",
    r'''
# DAMA Repository Hygiene

## Tracked

- Source code
- Documentation
- Frontend package lock
- Smoke tests
- Operator scripts

## Ignored

- backend/data
- backend/exports
- backend/backups
- frontend/node_modules
- frontend/.next
- frontend/out
- frontend/tsconfig.tsbuildinfo
- frontend/*.tsbuildinfo

## Check

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\repo-hygiene-check.ps1

## Note

Generated runtime files should remain local and should not be committed.
    ''',
)

append_once(
    "docs/project-status.md",
    "## Release Pack Q Completed",
    r'''
## Release Pack Q Completed

Name:

Repo Cleanup + Production Readiness

Added files:

- scripts/dev-backend.ps1
- scripts/dev-frontend.ps1
- scripts/dev-all.ps1
- scripts/repo-hygiene-check.ps1
- docs/local-development.md
- docs/production-readiness.md
- docs/repo-hygiene.md

Updated files:

- .gitignore
- README.md
- frontend/tsconfig.json
- scripts/frontend-check.ps1
- docs/project-status.md

Cleaned:

- frontend/tsconfig.tsbuildinfo removed from working tree
- frontend/tsconfig.tsbuildinfo ignored

Added behavior:

- local backend start script
- local frontend start script
- local full-stack start script
- repo hygiene check
- stronger frontend production-readiness check

Next recommended Release Pack:

Release Pack R: Dependency Audit + Security Baseline

Suggested scope:

- npm audit review
- safe non-breaking npm audit handling
- backend dependency freeze
- requirements lock snapshot
- security docs
- no force upgrades without review
    ''',
)

print("Release Pack Q applied successfully.")
