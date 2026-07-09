$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    return [string]::Join("`n", (Get-Content -LiteralPath $Path))
}

Write-Host "DAMA config baseline check started."

$RequiredFiles = @(
    ".\.env.example",
    ".\.gitignore",
    ".\backend\src\main.py",
    ".\frontend\package.json",
    ".\frontend\src\lib\api-client.ts",
    ".\docs\configuration.md",
    ".\docs\environment-checklist.md"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required config baseline file missing: $File"
    }
}

$EnvExample = Read-TextFile ".\.env.example"
$GitIgnore = Read-TextFile ".\.gitignore"
$ApiClient = Read-TextFile ".\frontend\src\lib\api-client.ts"
$MainPy = Read-TextFile ".\backend\src\main.py"

$RequiredEnvKeys = @(
    "DAMA_ENV",
    "DAMA_API_BASE_URL",
    "DAMA_FRONTEND_ORIGIN",
    "NEXT_PUBLIC_DAMA_API_BASE_URL",
    "DAMA_AI_PROVIDER",
    "DAMA_OLLAMA_BASE_URL",
    "DAMA_OLLAMA_DEFAULT_MODEL"
)

foreach ($Key in $RequiredEnvKeys) {
    if ($EnvExample -notmatch $Key) {
        throw ".env.example is missing required key: $Key"
    }
}

$RequiredIgnoreLines = @(
    ".env",
    ".env.*",
    "!.env.example",
    "backend/.env",
    "frontend/.env"
)

foreach ($Line in $RequiredIgnoreLines) {
    if ($GitIgnore -notmatch [regex]::Escape($Line)) {
        throw ".gitignore is missing env rule: $Line"
    }
}

if ($ApiClient -notmatch "NEXT_PUBLIC_DAMA_API_BASE_URL") {
    throw "Frontend API client does not use NEXT_PUBLIC_DAMA_API_BASE_URL."
}

if ($MainPy -notmatch "CORSMiddleware") {
    throw "Backend CORS middleware is missing."
}

if ($MainPy -notmatch "http://localhost:3000") {
    throw "Backend CORS does not include local frontend origin."
}

$TrackedFiles = git ls-files

$ForbiddenTracked = @(
    ".env",
    "backend/.env",
    "frontend/.env",
    "frontend/.env.local",
    "frontend/.env.production",
    "backend/.env.local",
    "backend/.env.production"
)

foreach ($File in $TrackedFiles) {
    foreach ($Forbidden in $ForbiddenTracked) {
        if ($File -eq $Forbidden) {
            throw "Real environment file is tracked and must be removed from git: $File"
        }
    }
}

Write-Host "DAMA config baseline check passed."
