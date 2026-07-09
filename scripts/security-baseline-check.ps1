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

Write-Host "DAMA security baseline check started."

$GitIgnore = Read-TextFile ".\.gitignore"
$PackageJson = Read-TextFile ".\frontend\package.json"
$MainPy = Read-TextFile ".\backend\src\main.py"

$RequiredIgnores = @(
    "frontend/node_modules/",
    "frontend/.next/",
    "frontend/tsconfig.tsbuildinfo",
    "backend/data/",
    "backend/exports/",
    "backend/backups/"
)

foreach ($Ignore in $RequiredIgnores) {
    if ($GitIgnore -notmatch [regex]::Escape($Ignore)) {
        throw ".gitignore is missing required ignore: $Ignore"
    }
}

if ($PackageJson -match '"next"\s*:\s*"latest"') {
    throw "frontend/package.json must not use next latest."
}

if ($PackageJson -match '"react"\s*:\s*"latest"') {
    throw "frontend/package.json must not use react latest."
}

if ($PackageJson -match '"react-dom"\s*:\s*"latest"') {
    throw "frontend/package.json must not use react-dom latest."
}

if ($MainPy -notmatch "CORSMiddleware") {
    throw "Backend CORS middleware is not configured."
}

if ($MainPy -notmatch "http://localhost:3000") {
    throw "Backend CORS does not include localhost frontend origin."
}

$TrackedFiles = git ls-files

foreach ($File in $TrackedFiles) {
    if ($File -like "frontend/.next/*") {
        throw "Tracked frontend build cache found: $File"
    }

    if ($File -like "frontend/node_modules/*") {
        throw "Tracked frontend node_modules file found: $File"
    }

    if ($File -like "backend/data/*") {
        throw "Tracked backend runtime database file found: $File"
    }

    if ($File -like "backend/exports/*") {
        throw "Tracked backend export file found: $File"
    }

    if ($File -like "backend/backups/*") {
        throw "Tracked backend backup file found: $File"
    }

    if ($File -eq "frontend/tsconfig.tsbuildinfo") {
        throw "Tracked TypeScript build cache found: $File"
    }
}

if ($TrackedFiles -contains ".env") {
    Write-Host "WARNING: .env is tracked. Review whether it contains secrets."
}

Write-Host "DAMA security baseline check passed."
