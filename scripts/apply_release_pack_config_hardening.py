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


def patch_gitignore() -> None:
    target = ROOT / ".gitignore"
    text = target.read_text(encoding="utf-8") if target.exists() else ""

    lines = [
        "",
        "# Environment files",
        ".env",
        ".env.*",
        "!.env.example",
        "backend/.env",
        "backend/.env.*",
        "!backend/.env.example",
        "frontend/.env",
        "frontend/.env.*",
        "!frontend/.env.example",
    ]

    for line in lines:
        if line and line not in text:
            text += "\n" + line

    target.write_text(text.strip() + "\n", encoding="utf-8")
    print("Updated .gitignore")


def patch_dama_check() -> None:
    target = ROOT / "scripts/dama-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "config-baseline-check.ps1" not in text:
        anchor = 'Write-Host "DAMA check completed."'
        block = r'''
Write-Host ""
Write-Host "Checking config baseline..."
try {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\config-baseline-check.ps1"
}
catch {
    throw "Config baseline check failed."
}

Write-Host "DAMA check completed."
'''.strip()

        if anchor in text:
            text = text.replace(anchor, block)
        else:
            text += "\n\n" + block + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/dama-check.ps1")


patch_gitignore()


write_file(
    ".env.example",
    r'''
# DAMA local environment example
# Copy this file to .env for local-only settings.
# Do not commit real .env files.

DAMA_ENV=local
DAMA_DEBUG=true

# Backend
DAMA_API_HOST=127.0.0.1
DAMA_API_PORT=8000
DAMA_API_BASE_URL=http://127.0.0.1:8000

# Frontend
DAMA_FRONTEND_ORIGIN=http://localhost:3000
NEXT_PUBLIC_DAMA_API_BASE_URL=http://127.0.0.1:8000

# Local AI Provider
DAMA_AI_PROVIDER=ollama
DAMA_OLLAMA_BASE_URL=http://127.0.0.1:11434
DAMA_OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b

# Local storage
DAMA_DATA_DIR=backend/data
DAMA_EXPORTS_DIR=backend/exports
DAMA_BACKUPS_DIR=backend/backups

# Production note:
# In production, use real secret management instead of committing secrets here.
    ''',
)


write_file(
    "scripts/config-baseline-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    return [string]::Join("`n", (Get-Content -LiteralPath $Path))
}

Write-Host "DAMA config baseline check started."

$RequiredFiles = @(
    ".\.env.example",
    ".\.gitignore",
    ".\backend\src\main.py",
    ".\frontend\package.json",
    ".\frontend\src\lib\api-client.ts",
    ".\docs\configuration.md",
    ".\docs\environment-checklist.md"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required config baseline file missing: $File"
    }
}

$EnvExample = Read-TextFile ".\.env.example"
$GitIgnore = Read-TextFile ".\.gitignore"
$ApiClient = Read-TextFile ".\frontend\src\lib\api-client.ts"
$MainPy = Read-TextFile ".\backend\src\main.py"

$RequiredEnvKeys = @(
    "DAMA_ENV",
    "DAMA_API_BASE_URL",
    "DAMA_FRONTEND_ORIGIN",
    "NEXT_PUBLIC_DAMA_API_BASE_URL",
    "DAMA_AI_PROVIDER",
    "DAMA_OLLAMA_BASE_URL",
    "DAMA_OLLAMA_DEFAULT_MODEL"
)

foreach ($Key in $RequiredEnvKeys) {
    if ($EnvExample -notmatch $Key) {
        throw ".env.example is missing required key: $Key"
    }
}

$RequiredIgnoreLines = @(
    ".env",
    ".env.*",
    "!.env.example",
    "backend/.env",
    "frontend/.env"
)

foreach ($Line in $RequiredIgnoreLines) {
    if ($GitIgnore -notmatch [regex]::Escape($Line)) {
        throw ".gitignore is missing env rule: $Line"
    }
}

if ($ApiClient -notmatch "NEXT_PUBLIC_DAMA_API_BASE_URL") {
    throw "Frontend API client does not use NEXT_PUBLIC_DAMA_API_BASE_URL."
}

if ($MainPy -notmatch "CORSMiddleware") {
    throw "Backend CORS middleware is missing."
}

if ($MainPy -notmatch "http://localhost:3000") {
    throw "Backend CORS does not include local frontend origin."
}

$TrackedFiles = git ls-files

$ForbiddenTracked = @(
    ".env",
    "backend/.env",
    "frontend/.env",
    "frontend/.env.local",
    "frontend/.env.production",
    "backend/.env.local",
    "backend/.env.production"
)

foreach ($File in $TrackedFiles) {
    foreach ($Forbidden in $ForbiddenTracked) {
        if ($File -eq $Forbidden) {
            throw "Real environment file is tracked and must be removed from git: $File"
        }
    }
}

Write-Host "DAMA config baseline check passed."
    ''',
)


write_file(
    "scripts/backend-requirements-snapshot.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $Root "backend"
$SnapshotPath = Join-Path $Root "docs\dependency-snapshots"

if (-not (Test-Path $SnapshotPath)) {
    New-Item -ItemType Directory -Path $SnapshotPath | Out-Null
}

$BackendPython = Join-Path $BackendPath ".venv\Scripts\python.exe"
$FreezePath = Join-Path $SnapshotPath "backend-pip-freeze.txt"
$RequirementsPath = Join-Path $BackendPath "requirements.txt"

Write-Host "DAMA backend requirements snapshot started."

if (-not (Test-Path $BackendPython)) {
    throw "Backend virtual environment was not found: $BackendPython"
}

& $BackendPython -m pip freeze 2>&1 | Set-Content -Path $FreezePath -Encoding UTF8

if (Test-Path $RequirementsPath) {
    Write-Host "backend/requirements.txt exists."
}
else {
    Write-Host "WARNING: backend/requirements.txt was not found."
}

Write-Host "Snapshot written:"
Write-Host $FreezePath
Write-Host "DAMA backend requirements snapshot completed."
    ''',
)


write_file(
    "docs/configuration.md",
    r'''
# DAMA Configuration

DAMA uses a local-first configuration baseline.

## Environment Example

The repository includes:

    .env.example

Copy it locally when needed:

    Copy-Item .\.env.example .\.env

Do not commit real `.env` files.

## Main Local Values

Backend URL:

    http://127.0.0.1:8000

Frontend URL:

    http://localhost:3000

Ollama URL:

    http://127.0.0.1:11434

Default local model:

    qwen2.5-coder:7b

## Frontend API Base URL

Frontend reads:

    NEXT_PUBLIC_DAMA_API_BASE_URL

Default:

    http://127.0.0.1:8000

## Backend CORS

Backend currently allows local frontend origins:

    http://localhost:3000
    http://127.0.0.1:3000
    http://localhost:3001
    http://127.0.0.1:3001

## Config Check

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\config-baseline-check.ps1

## Rule

Real secrets must not be committed.

Use `.env.example` only for safe defaults and documentation.
    ''',
)


write_file(
    "docs/environment-checklist.md",
    r'''
# DAMA Environment Checklist

## Local Backend

Required:

- Python virtual environment exists at `backend/.venv`
- FastAPI app imports successfully
- Uvicorn can run `src.main:app`
- Backend opens on `http://127.0.0.1:8000`

Command:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1

## Local Frontend

Required:

- Node.js installed
- npm.cmd available
- frontend/package-lock.json committed
- frontend/node_modules installed locally
- frontend builds successfully

Command:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1

## Local Ollama

Required:

- Ollama installed
- Ollama service running
- Model available locally

Recommended model:

    qwen2.5-coder:7b

## Checks

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check

Before shipping:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"

## Do Not Commit

- `.env`
- database files
- export files
- backup files
- frontend build output
- dependency folders
    ''',
)


write_file(
    "docs/backend-requirements-policy.md",
    r'''
# DAMA Backend Requirements Policy

## Source of Truth

Backend dependencies should be declared in:

    backend/requirements.txt

## Snapshot

A local freeze snapshot can be generated with:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-requirements-snapshot.ps1

Output:

    docs/dependency-snapshots/backend-pip-freeze.txt

## Policy

- Do not blindly upgrade backend dependencies.
- Prefer small patch upgrades.
- Run backend smoke tests after dependency changes.
- Run full DAMA ship check before committing dependency changes.

## Future Improvement

Before production deployment, add a stronger dependency locking strategy.

Options:

- pip-tools
- uv lock
- poetry lock

For now, DAMA uses a simple requirements file plus local freeze snapshots.
    ''',
)


append_once(
    "README.md",
    "## DAMA Configuration",
    r'''
## DAMA Configuration

Configuration example:

    .env.example

Copy locally if needed:

    Copy-Item .\.env.example .\.env

Run config baseline check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\config-baseline-check.ps1

Create backend dependency snapshot:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-requirements-snapshot.ps1
    ''',
)


append_once(
    "docs/production-readiness.md",
    "## Config Hardening",
    r'''
## Config Hardening

Release Pack S adds:

- .env.example
- environment ignore rules
- config baseline check
- backend requirements snapshot script
- configuration docs
- environment checklist
- backend requirements policy

This improves local development safety and prepares the project for later deployment hardening.
    ''',
)


append_once(
    "docs/security-baseline.md",
    "## Configuration Safety",
    r'''
## Configuration Safety

Release Pack S adds a configuration baseline.

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\config-baseline-check.ps1

This verifies:

- safe `.env.example`
- real env files are not tracked
- frontend uses `NEXT_PUBLIC_DAMA_API_BASE_URL`
- backend CORS baseline exists
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack S Completed",
    r'''
## Release Pack S Completed

Name:

Backend Requirements Lock + Config Hardening

Added files:

- .env.example
- scripts/config-baseline-check.ps1
- scripts/backend-requirements-snapshot.ps1
- docs/configuration.md
- docs/environment-checklist.md
- docs/backend-requirements-policy.md

Updated files:

- .gitignore
- README.md
- scripts/dama-check.ps1
- docs/production-readiness.md
- docs/security-baseline.md
- docs/project-status.md

Added behavior:

- config baseline check
- env file safety check
- frontend API env validation
- backend CORS validation
- backend dependency snapshot script

Next recommended Release Pack:

Release Pack T: Runtime Health UI + Dev Operator Dashboard

Suggested scope:

- frontend health page polish
- backend/frontend connection diagnostics
- Ollama model status panel
- database backup status panel
- environment status summary
- no destructive actions
    ''',
)


patch_dama_check()

print("Release Pack S applied successfully.")
