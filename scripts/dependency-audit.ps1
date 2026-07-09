$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path $Root "backend"
$FrontendPath = Join-Path $Root "frontend"
$SnapshotPath = Join-Path $Root "docs\dependency-snapshots"

if (-not (Test-Path $SnapshotPath)) {
    New-Item -ItemType Directory -Path $SnapshotPath | Out-Null
}

$BackendPython = Join-Path $BackendPath ".venv\Scripts\python.exe"
$BackendFreeze = Join-Path $SnapshotPath "backend-pip-freeze.txt"
$FrontendTree = Join-Path $SnapshotPath "frontend-npm-tree.txt"
$FrontendAudit = Join-Path $SnapshotPath "frontend-npm-audit.txt"
$Summary = Join-Path $SnapshotPath "dependency-audit-summary.txt"

Write-Host "DAMA dependency audit started."

if (Test-Path $BackendPython) {
    Write-Host "Writing backend pip freeze snapshot..."
    & $BackendPython -m pip freeze 2>&1 | Set-Content -Path $BackendFreeze -Encoding UTF8
}
else {
    "Backend virtual environment was not found." | Set-Content -Path $BackendFreeze -Encoding UTF8
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    "npm.cmd was not found. Install Node.js first." | Set-Content -Path $FrontendAudit -Encoding UTF8
    throw "npm.cmd was not found. Install Node.js first."
}

Set-Location $FrontendPath

if (-not (Test-Path ".\node_modules")) {
    Write-Host "Installing frontend dependencies before audit..."
    npm.cmd install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
}

Write-Host "Writing frontend dependency tree snapshot..."
npm.cmd ls --depth=0 2>&1 | Set-Content -Path $FrontendTree -Encoding UTF8
$TreeExit = $LASTEXITCODE

Write-Host "Running npm audit at high threshold..."
npm.cmd audit --audit-level=high 2>&1 | Set-Content -Path $FrontendAudit -Encoding UTF8
$AuditExit = $LASTEXITCODE

Set-Location $Root

$SummaryLines = @()
$SummaryLines += "DAMA Dependency Audit Summary"
$SummaryLines += "Generated locally"
$SummaryLines += ""
$SummaryLines += "Backend pip freeze:"
$SummaryLines += $BackendFreeze
$SummaryLines += ""
$SummaryLines += "Frontend npm tree:"
$SummaryLines += $FrontendTree
$SummaryLines += "npm ls exit code:"
$SummaryLines += $TreeExit
$SummaryLines += ""
$SummaryLines += "Frontend npm audit:"
$SummaryLines += $FrontendAudit
$SummaryLines += "npm audit exit code:"
$SummaryLines += $AuditExit
$SummaryLines += ""
$SummaryLines += "Audit policy:"
$SummaryLines += "- No npm audit fix --force"
$SummaryLines += "- No breaking dependency upgrades without review"
$SummaryLines += "- Moderate issues are documented first"
$SummaryLines += "- High/Critical issues should block release review"

$SummaryLines | Set-Content -Path $Summary -Encoding UTF8

if ($AuditExit -ne 0) {
    Write-Host ""
    Write-Host "npm audit reported high or critical issues."
    Write-Host "Review: docs\dependency-snapshots\frontend-npm-audit.txt"
    throw "npm audit found high or critical issues."
}

Write-Host "DAMA dependency audit completed."
