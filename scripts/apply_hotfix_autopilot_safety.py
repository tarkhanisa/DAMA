from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


write_file(
    "scripts/backend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\backend\.venv\Scripts\python.exe"
$BackendPath = Join-Path $Root "backend"

$env:PYTHONPATH = $BackendPath

$SmokeTests = @(
    ".\backend\tests\smoke_test_ai.py",
    ".\backend\tests\smoke_test_projects.py",
    ".\backend\tests\smoke_test_content_assets.py",
    ".\backend\tests\smoke_test_generation_storage.py",
    ".\backend\tests\smoke_test_project_workflow.py",
    ".\backend\tests\smoke_test_workflow_automation.py",
    ".\backend\tests\smoke_test_exports.py",
    ".\backend\tests\smoke_test_batch_generation.py",
    ".\backend\tests\smoke_test_dashboard.py",
    ".\backend\tests\smoke_test_maintenance.py",
    ".\backend\tests\smoke_test_developer.py"
)

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

foreach ($SmokeTest in $SmokeTests) {
    if (-not (Test-Path $SmokeTest)) {
        throw "Smoke test was not found at $SmokeTest"
    }
}

Write-Host "Running DAMA backend smoke tests..."
Write-Host "PYTHONPATH=$env:PYTHONPATH"

foreach ($SmokeTest in $SmokeTests) {
    Write-Host ""
    Write-Host "Running $SmokeTest..."
    & $PythonPath $SmokeTest

    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: $SmokeTest"
    }
}

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
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

if ($LASTEXITCODE -ne 0) {
    throw "Backend check failed."
}

Write-Host ""
Write-Host "Checking frontend foundation..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\frontend-check.ps1"

if ($LASTEXITCODE -ne 0) {
    throw "Frontend check failed."
}

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

if ($LASTEXITCODE -ne 0) {
    throw "DAMA check failed. Ship stopped."
}

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


print("Autopilot safety hotfix applied.")
