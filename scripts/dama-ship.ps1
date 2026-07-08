param(
    [Parameter(Mandatory = $true)]
    [string] $Message
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $Message.Trim()) {
    throw "Commit message cannot be empty."
}

Write-Host "DAMA ship started."

Write-Host ""
Write-Host "Running checks before shipping..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\dama-check.ps1"

Write-Host ""
Write-Host "Checking Git status..."
$Changes = git status --short

if (-not $Changes) {
    Write-Host "No changes to commit."
    exit 0
}

$Changes

Write-Host ""
Write-Host "Staging all changes..."
git add -A

if ($LASTEXITCODE -ne 0) {
    throw "git add failed."
}

Write-Host ""
Write-Host "Checking staged changes..."
git diff --cached --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "No staged changes to commit."
    exit 0
}

Write-Host ""
Write-Host "Committing..."
git commit -m $Message

if ($LASTEXITCODE -ne 0) {
    throw "git commit failed."
}

Write-Host ""
Write-Host "Pushing..."
git push

if ($LASTEXITCODE -ne 0) {
    throw "git push failed."
}

Write-Host ""
Write-Host "DAMA ship completed."
