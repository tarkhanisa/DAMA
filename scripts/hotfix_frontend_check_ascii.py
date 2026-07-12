from pathlib import Path

ROOT = Path("I:/DAMA")
target = ROOT / "scripts/frontend-check.ps1"

content = r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -Path $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path ".\frontend\node_modules")) {
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
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\generate\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\publishing\variants\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\wordpress\page.tsx",
    ".\frontend\src\app\publishing\telegram\page.tsx",
    ".\frontend\src\app\settings\page.tsx",
    ".\frontend\src\app\advanced\page.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$SettingsPage = Read-TextFile ".\frontend\src\app\settings\page.tsx"
$AdvancedPage = Read-TextFile ".\frontend\src\app\advanced\page.tsx"
$QueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$QueueForm = Read-TextFile ".\frontend\src\components\create-publishing-queue-item-form.tsx"
$QueueRunAction = Read-TextFile ".\frontend\src\components\run-publishing-queue-item-action.tsx"

$ExpectedNavRoutes = @(
    'href: "/"',
    'href: "/generate"',
    'href: "/publishing"',
    'href: "/projects"',
    'href: "/content-assets"',
    'href: "/settings"',
    'href: "/advanced"'
)

foreach ($Route in $ExpectedNavRoutes) {
    if ($AppNav -notmatch [regex]::Escape($Route)) {
        throw "Simplified navigation is missing route marker: $Route"
    }
}

$HiddenFromMainNav = @(
    'href: "/operations"',
    'href: "/runtime"',
    'href: "/exports"',
    'href: "/maintenance"',
    'href: "/workflows"',
    'href: "/search"'
)

foreach ($Route in $HiddenFromMainNav) {
    if ($AppNav -match [regex]::Escape($Route)) {
        throw "Technical route should not be in main nav: $Route"
    }
}

if ($HomePage -notmatch "/generate") {
    throw "Home page does not link to generate page."
}

if ($HomePage -notmatch "/publishing") {
    throw "Home page does not link to publishing page."
}

if ($PublishingPage -notmatch "/publishing/queue") {
    throw "Publishing page does not link to queue."
}

if ($PublishingPage -notmatch "/publishing/attempts") {
    throw "Publishing page does not link to attempts."
}

if ($SettingsPage -notmatch "/publishing/wordpress") {
    throw "Settings page does not link to WordPress."
}

if ($SettingsPage -notmatch "/publishing/telegram") {
    throw "Settings page does not link to Telegram."
}

if ($AdvancedPage -notmatch "/operations") {
    throw "Advanced page does not expose operations."
}

if ($AdvancedPage -notmatch "/runtime") {
    throw "Advanced page does not expose runtime."
}

if ($QueuePage -notmatch "/publishing/queue") {
    throw "Publishing queue page does not call queue endpoint."
}

if ($QueueForm -notmatch "/publishing/queue") {
    throw "Publishing queue form does not call queue endpoint."
}

if ($QueueRunAction -notmatch "/run") {
    throw "Publishing queue run action is missing run endpoint."
}

Write-Host "Frontend production readiness check passed."
'''

target.write_text(content.strip() + "\n", encoding="utf-8-sig")

print("frontend-check.ps1 rewritten as ASCII-only PowerShell with UTF-8 BOM.")
