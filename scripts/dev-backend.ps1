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
