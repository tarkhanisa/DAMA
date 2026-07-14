$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path -LiteralPath ".\frontend\node_modules")) {
    throw "frontend/node_modules not found. Run npm install in frontend first."
}

Write-Host "node_modules found. Running frontend typecheck..."

Push-Location ".\frontend"
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Frontend typecheck failed."
}
Pop-Location

$RequiredFiles = @(
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\safe-exit-action.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$SafeExitAction = Read-TextFile ".\frontend\src\components\safe-exit-action.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($AppNav -notmatch "safe-exit-top-button") {
    throw "App nav is missing sticky safe exit button."
}

if ($AppNav -notmatch "/publishing/operator/session/safe-exit") {
    throw "App nav safe exit button does not call backend safe exit endpoint."
}

if ($AppNav -notmatch "window.close") {
    throw "App nav safe exit does not attempt to close the browser tab."
}

if ($SafeExitAction -notmatch "window.close") {
    throw "Safe exit page does not attempt to close the browser tab."
}

if ($Styles -notmatch "Sticky red safe exit button") {
    throw "Global styles missing sticky red safe exit marker."
}

Write-Host "Frontend production readiness check passed."
