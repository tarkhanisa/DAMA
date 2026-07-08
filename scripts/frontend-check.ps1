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
    ".\frontend\src\app\projects\new\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\content-assets\new\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\dry-run\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx",
    ".\frontend\src\components\data-table.tsx",
    ".\frontend\src\components\status-pill.tsx",
    ".\frontend\src\components\action-card.tsx",
    ".\frontend\src\components\json-preview.tsx",
    ".\frontend\src\components\page-header.tsx",
    ".\frontend\src\components\error-panel.tsx",
    ".\frontend\src\components\form-status.tsx",
    ".\frontend\src\components\create-project-form.tsx",
    ".\frontend\src\components\create-content-asset-form.tsx",
    ".\frontend\src\components\workflow-dry-run-form.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$ProjectForm = Get-Content ".\frontend\src\components\create-project-form.tsx" -Raw
$AssetForm = Get-Content ".\frontend\src\components\create-content-asset-form.tsx" -Raw
$DryRunForm = Get-Content ".\frontend\src\components\workflow-dry-run-form.tsx" -Raw
$ProjectsPage = Get-Content ".\frontend\src\app\projects\page.tsx" -Raw
$AssetsPage = Get-Content ".\frontend\src\app\content-assets\page.tsx" -Raw

if ($ApiClient -notmatch "createProject") {
    throw "API client does not expose createProject."
}

if ($ApiClient -notmatch "createContentAsset") {
    throw "API client does not expose createContentAsset."
}

if ($ApiClient -notmatch "batchGenerateDryRun") {
    throw "API client does not expose batchGenerateDryRun."
}

if ($ProjectForm -notmatch '"use client"') {
    throw "CreateProjectForm is not a client component."
}

if ($AssetForm -notmatch '"use client"') {
    throw "CreateContentAssetForm is not a client component."
}

if ($DryRunForm -notmatch '"use client"') {
    throw "WorkflowDryRunForm is not a client component."
}

if ($ProjectsPage -notmatch "/projects/new") {
    throw "Projects page does not link to create project page."
}

if ($AssetsPage -notmatch "/content-assets/new") {
    throw "Content assets page does not link to create asset page."
}

if (Test-Path ".\frontend\node_modules") {
    Write-Host "node_modules found. Running frontend typecheck..."
    Push-Location ".\frontend"
    try {
        npm run typecheck
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend typecheck failed."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "node_modules not found. Skipping npm typecheck."
}

Write-Host "Frontend write UI shell check passed."
