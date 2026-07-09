$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

$BackendScript = Join-Path $Root "scripts\dev-backend.ps1"
$FrontendScript = Join-Path $Root "scripts\dev-frontend.ps1"

if (-not (Test-Path $BackendScript)) {
    throw "Backend dev script not found."
}

if (-not (Test-Path $FrontendScript)) {
    throw "Frontend dev script not found."
}

Write-Host "Opening DAMA backend and frontend in separate PowerShell windows..."

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-NoExit",
    "-File",
    $BackendScript
)

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-NoExit",
    "-File",
    $FrontendScript
)

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "API Docs: http://127.0.0.1:8000/docs"
