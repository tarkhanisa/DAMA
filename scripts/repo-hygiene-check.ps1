$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ForbiddenTrackedPatterns = @(
    "frontend/tsconfig.tsbuildinfo",
    "frontend/.next/",
    "frontend/node_modules/",
    "backend/data/",
    "backend/exports/",
    "backend/backups/"
)

$TrackedFiles = git ls-files

foreach ($Pattern in $ForbiddenTrackedPatterns) {
    foreach ($File in $TrackedFiles) {
        if ($File -like "$Pattern*") {
            throw "Forbidden tracked runtime/cache file found: $File"
        }
    }
}

Write-Host "Repo hygiene check passed."
