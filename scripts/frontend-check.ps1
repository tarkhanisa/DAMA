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
    ".\frontend\package-lock.json",
    ".\frontend\next.config.mjs",
    ".\frontend\tsconfig.json",
    ".\frontend\next-env.d.ts",
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
    ".\frontend\src\app\runtime\page.tsx",
    ".\frontend\src\components\generate-content-form.tsx",
    ".\frontend\src\app\generate\page.tsx",
    ".\frontend\src\components\create-publishing-channel-form.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\components\create-publishing-variants-form.tsx",
    ".\frontend\src\components\enhance-publishing-variant-action.tsx",
    ".\frontend\src\app\publishing\variants\page.tsx",
    ".\frontend\src\components\review-publishing-variant-form.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx",
    ".\frontend\src\components\create-wordpress-draft-action.tsx",
    ".\frontend\src\app\publishing\variants\[variantId]\page.tsx",
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

$GitIgnore = Read-TextFile ".\.gitignore"
$ApiClient = Read-TextFile ".\frontend\src\lib\api-client.ts"
$Nav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$SafeAction = Read-TextFile ".\frontend\src\components\safe-action-button.tsx"
$Operations = Read-TextFile ".\frontend\src\app\operations\page.tsx"
$ProjectDetail = Read-TextFile ".\frontend\src\app\projects\[projectId]\page.tsx"
$AssetDetail = Read-TextFile ".\frontend\src\app\content-assets\[assetId]\page.tsx"
$TsConfig = Read-TextFile ".\frontend\tsconfig.json"

if ($GitIgnore -notmatch "frontend/tsconfig.tsbuildinfo") {
    throw ".gitignore does not ignore frontend/tsconfig.tsbuildinfo."
}

if ($TsConfig -match '"incremental": true') {
    throw "frontend tsconfig should not use incremental true in this repo."
}

if ($ApiClient -notmatch "backupDatabase") {
    throw "API client does not expose backupDatabase."
}

if ($ApiClient -notmatch "searchProjects") {
    throw "API client does not expose searchProjects."
}

if ($ApiClient -notmatch "searchContentAssets") {
    throw "API client does not expose searchContentAssets."
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

$RuntimePage = Read-TextFile ".\frontend\src\app\runtime\page.tsx"

if ($RuntimePage -notmatch "/runtime/health") {
    throw "Runtime page does not include runtime health fetch."
}

$GeneratePage = Read-TextFile ".\frontend\src\app\generate\page.tsx"
$GenerateForm = Read-TextFile ".\frontend\src\components\generate-content-form.tsx"

if ($GeneratePage -notmatch "GenerateContentForm") {
    throw "Generate page does not include GenerateContentForm."
}

if ($GenerateForm -notmatch "save_output") {
    throw "Generate form does not expose save_output."
}

if ($GenerateForm -notmatch "/content/generate") {
    throw "Generate form does not call content generation endpoint."
}

if ($GenerateForm -notmatch "/workflows/projects/") {
    throw "Generate form does not include workflow generation fallback."
}

$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$PublishingForm = Read-TextFile ".\frontend\src\components\create-publishing-channel-form.tsx"

if ($PublishingPage -notmatch "CreatePublishingChannelForm") {
    throw "Publishing page does not include channel creation form."
}

if ($PublishingForm -notmatch "/publishing/channels") {
    throw "Publishing form does not call publishing channels endpoint."
}

$PublishingVariantsPage = Read-TextFile ".\frontend\src\app\publishing\variants\page.tsx"
$PublishingVariantsForm = Read-TextFile ".\frontend\src\components\create-publishing-variants-form.tsx"

if ($PublishingVariantsPage -notmatch "CreatePublishingVariantsForm") {
    throw "Publishing variants page does not include variant form."
}

if ($PublishingVariantsForm -notmatch "/publishing/variants/plan") {
    throw "Publishing variants form does not call variant plan endpoint."
}

$PublishingEnhancerAction = Read-TextFile ".\frontend\src\components\enhance-publishing-variant-action.tsx"

if ($PublishingEnhancerAction -notmatch "/publishing/variants/") {
    throw "Publishing variant enhancer action is missing variant endpoint."
}

if ($PublishingEnhancerAction -notmatch "/enhance") {
    throw "Publishing variant enhancer action is missing enhance endpoint."
}

$PublishingVariantDetailPage = Read-TextFile ".\frontend\src\app\publishing\variants\[variantId]\page.tsx"
$PublishingVariantReviewForm = Read-TextFile ".\frontend\src\components\review-publishing-variant-form.tsx"

if ($PublishingVariantDetailPage -notmatch "ReviewPublishingVariantForm") {
    throw "Publishing variant detail page does not include review form."
}

if ($PublishingVariantReviewForm -notmatch "/review") {
    throw "Publishing variant review form is missing review endpoint."
}

if ($PublishingVariantReviewForm -notmatch "approved") {
    throw "Publishing variant review form is missing approved status."
}

$WordPressDraftAction = Read-TextFile ".\frontend\src\components\create-wordpress-draft-action.tsx"
$PublishingAttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"

if ($WordPressDraftAction -notmatch "/wordpress/draft") {
    throw "WordPress draft action is missing connector endpoint."
}

if ($WordPressDraftAction -notmatch "dry_run") {
    throw "WordPress draft action must support dry_run mode."
}

if ($PublishingAttemptsPage -notmatch "/publishing/attempts") {
    throw "Publishing attempts page does not call attempts endpoint."
}

$PublishingAttemptDetailPage = Read-TextFile ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx"
$WordPressDraftAction = Read-TextFile ".\frontend\src\components\create-wordpress-draft-action.tsx"
$PublishingAttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"

if ($PublishingAttemptDetailPage -notmatch "wordpress_link") {
    throw "Publishing attempt detail page is missing WordPress draft link support."
}

if ($WordPressDraftAction -notmatch "seo_title") {
    throw "WordPress draft action is missing SEO title field."
}

if ($WordPressDraftAction -notmatch "meta_description") {
    throw "WordPress draft action is missing meta description field."
}

if ($PublishingAttemptsPage -notmatch "/publishing/attempts/") {
    throw "Publishing attempts page does not link to attempt detail page."
}

$TelegramPage = Read-TextFile ".\frontend\src\app\publishing\telegram\page.tsx"
$TelegramTestAction = Read-TextFile ".\frontend\src\components\telegram-connection-test-action.tsx"
$TelegramVariantAction = Read-TextFile ".\frontend\src\components\telegram-preview-test-send-action.tsx"

if ($TelegramPage -notmatch "/publishing/telegram/config") {
    throw "Telegram page does not call config endpoint."
}

if ($TelegramTestAction -notmatch "/publishing/telegram/test") {
    throw "Telegram connection test action does not call test endpoint."
}

if ($TelegramVariantAction -notmatch "/telegram/preview") {
    throw "Telegram variant action is missing preview endpoint."
}

if ($TelegramVariantAction -notmatch "/telegram/send-test") {
    throw "Telegram variant action is missing send-test endpoint."
}

Write-Host "Frontend production readiness check passed."
