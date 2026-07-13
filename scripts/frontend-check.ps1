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
    ".\frontend\src\components\cleanup-test-data-action.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
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

$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$OperatorWorkflow = Read-TextFile ".\frontend\src\lib\operator-workflow.ts"
$OperatorChecklist = Read-TextFile ".\frontend\src\components\operator-checklist.tsx"
$QueuePage = Read-TextFile ".\frontend\src\app\publishing\queue\page.tsx"
$AttemptsPage = Read-TextFile ".\frontend\src\app\publishing\attempts\page.tsx"
$AttemptDetailPage = Read-TextFile ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx"
$CleanupPage = Read-TextFile ".\frontend\src\app\advanced\cleanup\page.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($OperatorWorkflow -notmatch "buildOperatorChecklist") {
    throw "Operator workflow helper is missing checklist builder."
}

if ($OperatorWorkflow -notmatch "getOperatorNextAction") {
    throw "Operator workflow helper is missing next action resolver."
}

if ($OperatorChecklist -notmatch "next-action-card") {
    throw "Operator checklist component is missing next action card."
}

if ($HomePage -notmatch "OperatorChecklist") {
    throw "Home page is not rendering operator checklist."
}

if ($HomePage -notmatch "getOperatorNextAction") {
    throw "Home page is not using next action resolver."
}

if ($HomePage -notmatch "dashboard-flow") {
    throw "Home page is missing visual dashboard flow."
}

if ($QueuePage -notmatch "labelQueueStatus") {
    throw "Queue page is not using Persian queue labels."
}

if ($AttemptsPage -notmatch "labelAttemptStatus") {
    throw "Attempts page is not using Persian attempt labels."
}

if ($AttemptDetailPage -notmatch "technical-details") {
    throw "Attempt detail page is missing collapsible technical details."
}

if ($CleanupPage -notmatch "/publishing/cleanup/test-data/preview") {
    throw "Cleanup page does not call cleanup preview endpoint."
}

if ($Styles -notmatch "Guided operator checklist") {
    throw "Global styles are missing guided operator checklist marker."
}

Write-Host "Frontend production readiness check passed."
