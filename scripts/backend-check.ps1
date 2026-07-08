$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\backend\.venv\Scripts\python.exe"

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

foreach ($SmokeTest in $SmokeTests) {
    Write-Host ""
    Write-Host "Running $SmokeTest..."
    & $PythonPath $SmokeTest
}

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
