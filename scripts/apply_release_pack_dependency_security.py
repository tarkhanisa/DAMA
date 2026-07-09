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


def patch_dama_check() -> None:
    target = ROOT / "scripts/dama-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "repo-hygiene-check.ps1" not in text:
        text = text.replace(
            'Write-Host "DAMA check completed."',
            r'''
Write-Host ""
Write-Host "Checking repo hygiene..."
try {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\repo-hygiene-check.ps1"
}
catch {
    throw "Repo hygiene check failed."
}

Write-Host ""
Write-Host "Checking security baseline..."
try {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\security-baseline-check.ps1"
}
catch {
    throw "Security baseline check failed."
}

Write-Host "DAMA check completed."
'''.strip()
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/dama-check.ps1")


write_file(
    "scripts/dependency-audit.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $Root "backend"
$FrontendPath = Join-Path $Root "frontend"
$SnapshotPath = Join-Path $Root "docs\dependency-snapshots"

if (-not (Test-Path $SnapshotPath)) {
    New-Item -ItemType Directory -Path $SnapshotPath | Out-Null
}

$BackendPython = Join-Path $BackendPath ".venv\Scripts\python.exe"
$BackendFreeze = Join-Path $SnapshotPath "backend-pip-freeze.txt"
$FrontendTree = Join-Path $SnapshotPath "frontend-npm-tree.txt"
$FrontendAudit = Join-Path $SnapshotPath "frontend-npm-audit.txt"
$Summary = Join-Path $SnapshotPath "dependency-audit-summary.txt"

Write-Host "DAMA dependency audit started."

if (Test-Path $BackendPython) {
    Write-Host "Writing backend pip freeze snapshot..."
    cmd.exe /c ""$BackendPython" -m pip freeze > "$BackendFreeze" 2>&1"
}
else {
    "Backend virtual environment was not found." | Set-Content -Path $BackendFreeze -Encoding UTF8
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    "npm.cmd was not found. Install Node.js first." | Set-Content -Path $FrontendAudit -Encoding UTF8
    throw "npm.cmd was not found. Install Node.js first."
}

Set-Location $FrontendPath

if (-not (Test-Path ".\node_modules")) {
    Write-Host "Installing frontend dependencies before audit..."
    npm.cmd install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
}

Write-Host "Writing frontend dependency tree snapshot..."
cmd.exe /c "npm.cmd ls --depth=0 > "$FrontendTree" 2>&1"

Write-Host "Running npm audit at high threshold..."
cmd.exe /c "npm.cmd audit --audit-level=high > "$FrontendAudit" 2>&1"
$AuditExit = $LASTEXITCODE

Set-Location $Root

$SummaryLines = @()
$SummaryLines += "DAMA Dependency Audit Summary"
$SummaryLines += "Generated locally"
$SummaryLines += ""
$SummaryLines += "Backend pip freeze:"
$SummaryLines += $BackendFreeze
$SummaryLines += ""
$SummaryLines += "Frontend npm tree:"
$SummaryLines += $FrontendTree
$SummaryLines += ""
$SummaryLines += "Frontend npm audit:"
$SummaryLines += $FrontendAudit
$SummaryLines += ""
$SummaryLines += "Audit policy:"
$SummaryLines += "- No npm audit fix --force"
$SummaryLines += "- No breaking dependency upgrades without review"
$SummaryLines += "- Moderate issues are documented first"
$SummaryLines += "- High/Critical issues should block release review"
$SummaryLines += ""
$SummaryLines += "npm audit exit code:"
$SummaryLines += $AuditExit

$SummaryLines | Set-Content -Path $Summary -Encoding UTF8

if ($AuditExit -ne 0) {
    throw "npm audit found high or critical issues. Review docs\dependency-snapshots\frontend-npm-audit.txt"
}

Write-Host "DAMA dependency audit completed."
    ''',
)


write_file(
    "scripts/security-baseline-check.ps1",
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

Write-Host "DAMA security baseline check started."

$GitIgnore = Read-TextFile ".\.gitignore"
$PackageJson = Read-TextFile ".\frontend\package.json"
$MainPy = Read-TextFile ".\backend\src\main.py"

$RequiredIgnores = @(
    "frontend/node_modules/",
    "frontend/.next/",
    "frontend/tsconfig.tsbuildinfo",
    "backend/data/",
    "backend/exports/",
    "backend/backups/"
)

foreach ($Ignore in $RequiredIgnores) {
    if ($GitIgnore -notmatch [regex]::Escape($Ignore)) {
        throw ".gitignore is missing required ignore: $Ignore"
    }
}

if ($PackageJson -match '"next"\s*:\s*"latest"') {
    throw "frontend/package.json must not use next latest."
}

if ($PackageJson -match '"react"\s*:\s*"latest"') {
    throw "frontend/package.json must not use react latest."
}

if ($PackageJson -match '"react-dom"\s*:\s*"latest"') {
    throw "frontend/package.json must not use react-dom latest."
}

if ($MainPy -notmatch "CORSMiddleware") {
    throw "Backend CORS middleware is not configured."
}

if ($MainPy -notmatch "http://localhost:3000") {
    throw "Backend CORS does not include localhost frontend origin."
}

$TrackedFiles = git ls-files

foreach ($File in $TrackedFiles) {
    if ($File -like "frontend/.next/*") {
        throw "Tracked frontend build cache found: $File"
    }

    if ($File -like "frontend/node_modules/*") {
        throw "Tracked frontend node_modules file found: $File"
    }

    if ($File -like "backend/data/*") {
        throw "Tracked backend runtime database file found: $File"
    }

    if ($File -like "backend/exports/*") {
        throw "Tracked backend export file found: $File"
    }

    if ($File -like "backend/backups/*") {
        throw "Tracked backend backup file found: $File"
    }

    if ($File -eq "frontend/tsconfig.tsbuildinfo") {
        throw "Tracked TypeScript build cache found: $File"
    }
}

if ($TrackedFiles -contains ".env") {
    Write-Host "WARNING: .env is tracked. Review whether it contains secrets."
}

Write-Host "DAMA security baseline check passed."
    ''',
)


write_file(
    "docs/security-baseline.md",
    r'''
# DAMA Security Baseline

DAMA now has a local security baseline for development.

## Current Safety Defaults

- Runtime database files are ignored.
- Export files are ignored.
- Backup files are ignored.
- Frontend build caches are ignored.
- Frontend dependencies are pinned away from floating latest versions.
- Frontend has a package-lock file.
- Backend has CORS configured only for local frontend development origins.
- Destructive UI operations are intentionally not exposed.
- Operations UI uses confirmation-first actions.

## Local Security Checks

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security-baseline-check.ps1

This checks:

- required .gitignore entries
- pinned frontend dependencies
- CORS presence
- tracked runtime/cache files

## Dependency Audit

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

This creates snapshots in:

    docs/dependency-snapshots/

## Policy

Do not run:

    npm audit fix --force

without reviewing the breaking changes first.
    ''',
)


write_file(
    "docs/dependency-policy.md",
    r'''
# DAMA Dependency Policy

## Core Rule

DAMA prioritizes reproducible local builds over newest possible package versions.

## Frontend

Frontend packages should not use floating `latest`.

Current policy:

- Keep Next.js pinned to a stable major line.
- Keep React pinned to a stable major line.
- Commit package-lock.json.
- Do not run npm audit fix --force without review.

## Backend

Backend dependencies are managed through:

    backend/requirements.txt

A local freeze snapshot can be generated through:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

Snapshot output:

    docs/dependency-snapshots/backend-pip-freeze.txt

## Vulnerability Handling

Recommended order:

1. Record audit result.
2. Identify affected package.
3. Check whether the package is direct or transitive.
4. Prefer non-breaking patch/minor upgrades.
5. Avoid force upgrades unless the project can be tested immediately.
6. Run full DAMA ship check after dependency changes.

## Current npm Audit Note

If npm reports moderate vulnerabilities, document them first.

Do not use `npm audit fix --force` as an automatic step.
    ''',
)


write_file(
    "docs/dependency-snapshots/README.md",
    r'''
# Dependency Snapshots

This folder stores local dependency audit snapshots.

Generated by:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

Expected files:

- backend-pip-freeze.txt
- frontend-npm-tree.txt
- frontend-npm-audit.txt
- dependency-audit-summary.txt

These files are useful for release review and troubleshooting.
    ''',
)


append_once(
    "docs/production-readiness.md",
    "## Security Baseline",
    r'''
## Security Baseline

Release Pack R adds:

- security baseline check
- dependency audit script
- dependency snapshot folder
- dependency policy
- npm audit policy
- no-force upgrade rule

This does not make DAMA production-secure yet. It creates a safer local development baseline before deployment work.
    ''',
)


append_once(
    "docs/repo-hygiene.md",
    "## Security Baseline Check",
    r'''
## Security Baseline Check

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security-baseline-check.ps1

This check verifies pinned frontend dependency policy, ignored runtime folders, and CORS baseline.
    ''',
)


append_once(
    "README.md",
    "## DAMA Security and Dependency Checks",
    r'''
## DAMA Security and Dependency Checks

Run repo hygiene check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\repo-hygiene-check.ps1

Run security baseline check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security-baseline-check.ps1

Run dependency audit snapshot:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

Do not run npm audit fix --force without review.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack R Completed",
    r'''
## Release Pack R Completed

Name:

Dependency Audit + Security Baseline

Added files:

- scripts/dependency-audit.ps1
- scripts/security-baseline-check.ps1
- docs/security-baseline.md
- docs/dependency-policy.md
- docs/dependency-snapshots/README.md

Updated files:

- scripts/dama-check.ps1
- README.md
- docs/production-readiness.md
- docs/repo-hygiene.md
- docs/project-status.md

Added behavior:

- security baseline check
- dependency audit snapshot script
- high/critical npm audit threshold
- backend pip freeze snapshot generation
- frontend dependency tree snapshot generation
- pinned dependency policy docs
- no-force audit policy

Next recommended Release Pack:

Release Pack S: Backend Requirements Lock + Config Hardening

Suggested scope:

- backend requirements freeze snapshot
- config validation improvements
- environment docs
- .env.example review
- production config checklist
    ''',
)

patch_dama_check()

print("Release Pack R applied successfully.")
