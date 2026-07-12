from pathlib import Path

ROOT = Path("I:/DAMA")
target = ROOT / "scripts/frontend-check.ps1"

target.write_text(
r'''
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

if ($AppNav -notmatch "/generate") {
    throw "Navigation does not include تولید محتوا."
}

if ($AppNav -notmatch "/publishing") {
    throw "Navigation does not include انتشار."
}

if ($AppNav -notmatch "/settings") {
    throw "Navigation does not include تنظیمات."
}

if ($AppNav -notmatch "/advanced") {
    throw "Navigation does not include پیشرفته."
}

if ($AppNav -notmatch "داشبورد") {
    throw "Navigation is missing Persian dashboard label."
}

if ($AppNav -notmatch "تولید محتوا") {
    throw "Navigation is missing Persian generate label."
}

if ($AppNav -notmatch "انتشار") {
    throw "Navigation is missing Persian publishing label."
}

if ($AppNav -notmatch "تنظیمات") {
    throw "Navigation is missing Persian settings label."
}

if ($AppNav -notmatch "پیشرفته") {
    throw "Navigation is missing Persian advanced label."
}

if ($HomePage -notmatch "داشبورد ساده عملیات محتوا") {
    throw "Home page is not using the simplified Persian operator dashboard."
}

if ($PublishingPage -notmatch "مرکز ساده انتشار") {
    throw "Publishing page is not using the simplified Persian publishing center."
}

if ($SettingsPage -notmatch "/publishing/wordpress") {
    throw "Settings page does not link to WordPress settings."
}

if ($SettingsPage -notmatch "/publishing/telegram") {
    throw "Settings page does not link to Telegram settings."
}

if ($AdvancedPage -notmatch "/operations") {
    throw "Advanced page does not expose operations under پیشرفته."
}

if ($AdvancedPage -notmatch "/runtime") {
    throw "Advanced page does not expose runtime under پیشرفته."
}

if ($QueuePage -notmatch "/publishing/queue") {
    throw "Publishing queue page does not call queue endpoint."
}

Write-Host "Frontend production readiness check passed."
'''.strip() + "`n",
encoding="utf-8"
)

print("frontend-check.ps1 updated for Persian minimal operator UX.")
