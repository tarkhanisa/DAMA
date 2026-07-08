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

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

if (-not (Test-Path $AISmokeTestPath)) {
    throw "AI smoke test was not found at $AISmokeTestPath"
}

if (-not (Test-Path $ProjectSmokeTestPath)) {
    throw "Project smoke test was not found at $ProjectSmokeTestPath"
}

if (-not (Test-Path $ContentAssetSmokeTestPath)) {
    throw "Content asset smoke test was not found at $ContentAssetSmokeTestPath"
}

if (-not (Test-Path $GenerationStorageSmokeTestPath)) {
    throw "Generation storage smoke test was not found at $GenerationStorageSmokeTestPath"
}

if (-not (Test-Path $ProjectWorkflowSmokeTestPath)) {
    throw "Project workflow smoke test was not found at $ProjectWorkflowSmokeTestPath"
}

if (-not (Test-Path $WorkflowAutomationSmokeTestPath)) {
    throw "Workflow automation smoke test was not found at $WorkflowAutomationSmokeTestPath"
}

if (-not (Test-Path $ExportSmokeTestPath)) {
    throw "Export smoke test was not found at $ExportSmokeTestPath"
}

Write-Host "Running DAMA backend AI smoke test..."
& $PythonPath $AISmokeTestPath

Write-Host ""
Write-Host "Running DAMA project persistence smoke test..."
& $PythonPath $ProjectSmokeTestPath

Write-Host ""
Write-Host "Running DAMA content asset smoke test..."
& $PythonPath $ContentAssetSmokeTestPath

Write-Host ""
Write-Host "Running DAMA generation storage smoke test..."
& $PythonPath $GenerationStorageSmokeTestPath

Write-Host ""
Write-Host "Running DAMA project workflow smoke test..."
& $PythonPath $ProjectWorkflowSmokeTestPath

Write-Host ""
Write-Host "Running DAMA workflow automation smoke test..."
& $PythonPath $WorkflowAutomationSmokeTestPath

Write-Host ""
Write-Host "Running DAMA export smoke test..."
& $PythonPath $ExportSmokeTestPath

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
