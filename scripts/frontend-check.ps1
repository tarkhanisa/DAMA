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
    ".\frontend\src\lib\persian-copy.ts",
    ".\frontend\src\lib\operator-workflow.ts",
    ".\frontend\src\components\operator-checklist.tsx",
    ".\frontend\src\components\create-media-campaign-form.tsx",
    ".\frontend\src\components\cleanup-test-data-action.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\publishing\campaigns\page.tsx",
    ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx",
    ".\frontend\src\app\advanced\cleanup\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$CampaignsPage = Read-TextFile ".\frontend\src\app\publishing\campaigns\page.tsx"
$CampaignDetailPage = Read-TextFile ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx"
$CampaignForm = Read-TextFile ".\frontend\src\components\create-media-campaign-form.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($PublishingPage -notmatch "/publishing/campaigns") {
    throw "Publishing page does not link to media campaigns."
}

if ($CampaignsPage -notmatch "/publishing/campaigns") {
    throw "Campaigns page does not call campaigns endpoint."
}

if ($CampaignsPage -notmatch "CreateMediaCampaignForm") {
    throw "Campaigns page is missing campaign form."
}

if ($CampaignDetailPage -notmatch "media_items") {
    throw "Campaign detail page does not show media items."
}

if ($CampaignForm -notmatch "channel_ids") {
    throw "Campaign form does not submit selected channels."
}

if ($Styles -notmatch "Media campaign composer") {
    throw "Global styles are missing media campaign composer marker."
}

Write-Host "Frontend production readiness check passed."
