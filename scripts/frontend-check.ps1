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
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
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
    ".\frontend\src\components\status-pill.tsx",
    ".\frontend\src\components\action-card.tsx",
    ".\frontend\src\components\json-preview.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$Nav = Get-Content ".\frontend\src\components\app-nav.tsx" -Raw
$WorkflowsPage = Get-Content ".\frontend\src\app\workflows\page.tsx" -Raw
$ExportsPage = Get-Content ".\frontend\src\app\exports\page.tsx" -Raw
$MaintenancePage = Get-Content ".\frontend\src\app\maintenance\page.tsx" -Raw

if ($ApiClient -notmatch "projectOutputPlan") {
    throw "API client does not expose projectOutputPlan."
}

if ($ApiClient -notmatch "maintenanceStatus") {
    throw "API client does not expose maintenanceStatus."
}

if ($Nav -notmatch "/workflows") {
    throw "Navigation does not include workflows."
}

if ($Nav -notmatch "/exports") {
    throw "Navigation does not include exports."
}

if ($Nav -notmatch "/maintenance") {
    throw "Navigation does not include maintenance."
}

if ($WorkflowsPage -notmatch "damaApi.projects") {
    throw "Workflows page does not load projects."
}

if ($ExportsPage -notmatch "dashboardSummary") {
    throw "Exports page does not load dashboard summary."
}

if ($MaintenancePage -notmatch "maintenanceStatus") {
    throw "Maintenance page does not load maintenance status."
}

Write-Host "Frontend workflow/export/maintenance UI check passed."
