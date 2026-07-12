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
    ".\backend\tests\smoke_test_developer.py",
    ".\backend\tests\smoke_test_search.py",
    ".\backend\tests\smoke_test_runtime.py",
    ".\backend\tests\smoke_test_publishing.py",
    ".\backend\tests\smoke_test_publishing_variants.py",
    ".\backend\tests\smoke_test_publishing_ai_enhancer.py",
    ".\backend\tests\smoke_test_publishing_review.py",
    ".\backend\tests\smoke_test_wordpress_draft_connector.py"
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

$WordPressFlowPolishSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_wordpress_flow_polish.py"
$WordPressFlowPolishPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $WordPressFlowPolishSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_wordpress_flow_polish.py..."
    & $WordPressFlowPolishPython $WordPressFlowPolishSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_wordpress_flow_polish.py"
    }
}

$LocalEnvLoaderSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_local_env_loader.py"
$LocalEnvLoaderPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $LocalEnvLoaderSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_local_env_loader.py..."
    & $LocalEnvLoaderPython $LocalEnvLoaderSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_local_env_loader.py"
    }
}

$TelegramConnectorSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_telegram_connector.py"
$TelegramConnectorPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $TelegramConnectorSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_telegram_connector.py..."
    & $TelegramConnectorPython $TelegramConnectorSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_telegram_connector.py"
    }
}

$PublishingQueueSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_publishing_queue.py"
$PublishingQueuePython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $PublishingQueueSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_publishing_queue.py..."
    & $PublishingQueuePython $PublishingQueueSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_publishing_queue.py"
    }
}

