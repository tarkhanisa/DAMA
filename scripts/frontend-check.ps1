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
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        throw "Frontend foundation file is missing: $File"
    }
}

$DashboardPage = Get-Content ".\frontend\src\app\page.tsx" -Raw

if ($DashboardPage -notmatch "dashboardSummary") {
    throw "Dashboard page does not use dashboardSummary API client."
}

if ($DashboardPage -notmatch "ReadinessPanel") {
    throw "Dashboard page does not render ReadinessPanel."
}

Write-Host "Frontend dashboard check passed."
