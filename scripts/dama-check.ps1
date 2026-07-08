$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "DAMA check started."

Write-Host ""
Write-Host "Checking backend..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\backend-check.ps1"

if ($LASTEXITCODE -ne 0) {
    throw "Backend check failed."
}

Write-Host ""
Write-Host "Checking frontend foundation..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\frontend-check.ps1"

if ($LASTEXITCODE -ne 0) {
    throw "Frontend check failed."
}

Write-Host ""
Write-Host "DAMA check completed."
