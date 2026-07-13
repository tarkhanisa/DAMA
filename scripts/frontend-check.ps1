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
    ".\frontend\src\components\simple-publish-wizard-form.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\produce\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\other\page.tsx",
    ".\frontend\src\app\publishing\campaigns\page.tsx",
    ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$ProducePage = Read-TextFile ".\frontend\src\app\produce\page.tsx"
$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$OtherPage = Read-TextFile ".\frontend\src\app\other\page.tsx"
$PublishWizard = Read-TextFile ".\frontend\src\components\simple-publish-wizard-form.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

$ExpectedTopRoutes = @(
    'href: "/"',
    'href: "/produce"',
    'href: "/publishing"',
    'href: "/other"'
)

foreach ($Route in $ExpectedTopRoutes) {
    if ($AppNav -notmatch [regex]::Escape($Route)) {
        throw "Main nav missing route: $Route"
    }
}

if ($HomePage -notmatch "three-door-console") {
    throw "Home page is missing three-door console."
}

if ($ProducePage -notmatch "/generate") {
    throw "Produce page does not link to generation."
}

if ($PublishingPage -notmatch "SimplePublishWizardForm") {
    throw "Publishing page is missing simplified publish wizard."
}

if ($PublishWizard -notmatch "/publishing/campaigns") {
    throw "Publish wizard does not create campaigns."
}

if ($PublishWizard -notmatch "channel_ids") {
    throw "Publish wizard does not submit selected channels."
}

if ($OtherPage -notmatch "/advanced/cleanup") {
    throw "Other page does not link to cleanup."
}

if ($OtherPage -notmatch "/publishing/attempts") {
    throw "Other page does not link to publishing attempts."
}

if ($Styles -notmatch "Three door operator console") {
    throw "Global styles missing three-door marker."
}

Write-Host "Frontend production readiness check passed."
