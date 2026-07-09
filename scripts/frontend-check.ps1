$ErrorActionPreference = "Stop"


function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    return [string]::Join("`n", (Get-Content -LiteralPath $Path))
}


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
    ".\frontend\src\app\content-assets\[assetId]\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\dry-run\page.tsx",
    ".\frontend\src\app\search\page.tsx",
    ".\frontend\src\app\search\projects\page.tsx",
    ".\frontend\src\app\search\content-assets\page.tsx",
    ".\frontend\src\app\operations\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\safe-action-button.tsx",
    ".\frontend\src\components\operation-result.tsx",
    ".\frontend\src\components\backup-action.tsx",
    ".\frontend\src\components\export-project-action.tsx",
    ".\frontend\src\components\export-content-asset-action.tsx",
    ".\frontend\src\components\project-status-form.tsx",
    ".\frontend\src\components\content-asset-status-form.tsx",
    ".\frontend\src\components\search-filter-card.tsx",
    ".\frontend\src\components\asset-body-preview.tsx",
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

$ApiClient = Read-TextFile ".\frontend\src\lib\api-client.ts"
$Nav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$SafeAction = Read-TextFile ".\frontend\src\components\safe-action-button.tsx"
$Operations = Read-TextFile ".\frontend\src\app\operations\page.tsx"
$ProjectDetail = Read-TextFile ".\frontend\src\app\projects\[projectId]\page.tsx"
$AssetDetail = Read-TextFile ".\frontend\src\app\content-assets\[assetId]\page.tsx"

if ($ApiClient -notmatch "backupDatabase") {
    throw "API client does not expose backupDatabase."
}

if ($ApiClient -notmatch "exportProjectBundle") {
    throw "API client does not expose exportProjectBundle."
}

if ($ApiClient -notmatch "exportContentAssetMarkdown") {
    throw "API client does not expose exportContentAssetMarkdown."
}

if ($ApiClient -notmatch "updateProjectStatus") {
    throw "API client does not expose updateProjectStatus."
}

if ($ApiClient -notmatch "updateContentAssetStatus") {
    throw "API client does not expose updateContentAssetStatus."
}

if ($Nav -notmatch "/operations") {
    throw "Navigation does not include operations."
}

if ($SafeAction -notmatch "Confirm") {
    throw "SafeActionButton does not include confirmation behavior."
}

if ($Operations -notmatch "BackupAction") {
    throw "Operations page does not include backup action."
}

if ($ProjectDetail -notmatch "ProjectStatusForm") {
    throw "Project detail page does not include status form."
}

if ($AssetDetail -notmatch "ContentAssetStatusForm") {
    throw "Content asset detail page does not include status form."
}

if (Test-Path ".\frontend\node_modules") {
    Write-Host "node_modules found. Running frontend typecheck..."
    Push-Location ".\frontend"
    try {
        npm.cmd run typecheck
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

Write-Host "Frontend safe operational actions check passed."
