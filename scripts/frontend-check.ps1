$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RequiredFiles = @(
    ".\frontend\README.md",
    ".\frontend\package.json",
    ".\frontend\next.config.mjs",
    ".\frontend\tsconfig.json",
    ".\frontend\src\app\layout.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\projects\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx",
    ".\frontend\src\components\data-table.tsx",
    ".\frontend\src\components\status-pill.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$DashboardPage = Get-Content ".\frontend\src\app\page.tsx" -Raw
$ProjectsPage = Get-Content ".\frontend\src\app\projects\page.tsx" -Raw
$AssetsPage = Get-Content ".\frontend\src\app\content-assets\page.tsx" -Raw

if ($ApiClient -notmatch "projects") {
    throw "API client does not expose projects."
}

if ($ApiClient -notmatch "contentAssets") {
    throw "API client does not expose contentAssets."
}

if ($DashboardPage -notmatch "dashboardSummary") {
    throw "Dashboard page does not use dashboardSummary API client."
}

if ($ProjectsPage -notmatch "damaApi.projects") {
    throw "Projects page does not use projects API client."
}

if ($AssetsPage -notmatch "damaApi.contentAssets") {
    throw "Content assets page does not use contentAssets API client."
}

Write-Host "Frontend UI check passed."
