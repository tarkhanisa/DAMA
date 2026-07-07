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

Write-Host "Running DAMA AI smoke test..." -ForegroundColor Cyan

Set-Location $BackendPath
& $PythonPath $SmokeTestPath

Write-Host "DAMA AI smoke test completed successfully." -ForegroundColor Green
