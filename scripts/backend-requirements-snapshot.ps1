$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $Root "backend"
$SnapshotPath = Join-Path $Root "docs\dependency-snapshots"

if (-not (Test-Path $SnapshotPath)) {
    New-Item -ItemType Directory -Path $SnapshotPath | Out-Null
}

$BackendPython = Join-Path $BackendPath ".venv\Scripts\python.exe"
$FreezePath = Join-Path $SnapshotPath "backend-pip-freeze.txt"
$RequirementsPath = Join-Path $BackendPath "requirements.txt"

Write-Host "DAMA backend requirements snapshot started."

if (-not (Test-Path $BackendPython)) {
    throw "Backend virtual environment was not found: $BackendPython"
}

& $BackendPython -m pip freeze 2>&1 | Set-Content -Path $FreezePath -Encoding UTF8

if (Test-Path $RequirementsPath) {
    Write-Host "backend/requirements.txt exists."
}
else {
    Write-Host "WARNING: backend/requirements.txt was not found."
}

Write-Host "Snapshot written:"
Write-Host $FreezePath
Write-Host "DAMA backend requirements snapshot completed."
