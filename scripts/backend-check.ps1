$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\backend\.venv\Scripts\python.exe"
$AISmokeTestPath = ".\backend\tests\smoke_test_ai.py"
$ProjectSmokeTestPath = ".\backend\tests\smoke_test_projects.py"
$ContentAssetSmokeTestPath = ".\backend\tests\smoke_test_content_assets.py"
$GenerationStorageSmokeTestPath = ".\backend\tests\smoke_test_generation_storage.py"
$ProjectWorkflowSmokeTestPath = ".\backend\tests\smoke_test_project_workflow.py"
$WorkflowAutomationSmokeTestPath = ".\backend\tests\smoke_test_workflow_automation.py"
$ExportSmokeTestPath = ".\backend\tests\smoke_test_exports.py"
$BatchGenerationSmokeTestPath = ".\backend\tests\smoke_test_batch_generation.py"
$DashboardSmokeTestPath = ".\backend\tests\smoke_test_dashboard.py"
$MaintenanceSmokeTestPath = ".\backend\tests\smoke_test_maintenance.py"

$SmokeTests = @(
    $AISmokeTestPath,
    $ProjectSmokeTestPath,
    $ContentAssetSmokeTestPath,
    $GenerationStorageSmokeTestPath,
    $ProjectWorkflowSmokeTestPath,
    $WorkflowAutomationSmokeTestPath,
    $ExportSmokeTestPath,
    $BatchGenerationSmokeTestPath,
    $DashboardSmokeTestPath,
    $MaintenanceSmokeTestPath
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
