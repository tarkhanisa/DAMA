Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$PythonPath = Join-Path $BackendPath ".venv\Scripts\python.exe"
$SmokeTestPath = Join-Path $BackendPath "tests\smoke_test_ai.py"

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at: $PythonPath"
}

if (-not (Test-Path $SmokeTestPath)) {
    throw "Smoke test file was not found at: $SmokeTestPath"
}

Write-Host "Running DAMA backend smoke test..." -ForegroundColor Cyan

Set-Location $BackendPath
& $PythonPath $SmokeTestPath

Write-Host ""
Write-Host "Smoke test passed." -ForegroundColor Green
Write-Host ""
Write-Host "Git status:" -ForegroundColor Cyan

Set-Location $ProjectRoot
git status
