$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$FrontendPath = Join-Path $Root "frontend"

Set-Location $FrontendPath

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd was not found. Install Node.js first."
}

if (-not (Test-Path ".\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm.cmd install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
}

Write-Host "Starting DAMA frontend on http://localhost:3000"
npm.cmd run dev
