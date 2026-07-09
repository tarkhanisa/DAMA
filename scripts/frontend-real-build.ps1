$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $Root "frontend"

Set-Location $FrontendPath

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Install Node.js first."
}

Write-Host "Installing frontend dependencies..."
npm.cmd install
if ($LASTEXITCODE -ne 0) {
    throw "npm.cmd install failed."
}

Write-Host "Running frontend typecheck..."
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) {
    throw "Frontend typecheck failed."
}

Write-Host "Running frontend build..."
npm.cmd run build
if ($LASTEXITCODE -ne 0) {
    throw "Frontend build failed."
}

Write-Host "Frontend real build completed."
