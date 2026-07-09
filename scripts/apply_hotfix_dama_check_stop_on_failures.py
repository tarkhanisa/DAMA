from pathlib import Path

ROOT = Path("I:/DAMA")

target = ROOT / "scripts/dama-check.ps1"

target.write_text(
r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-DamaCheckScript {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Label,

        [Parameter(Mandatory=$true)]
        [string]$ScriptPath
    )

    Write-Host ""
    Write-Host $Label

    if (-not (Test-Path $ScriptPath)) {
        throw "Check script not found: $ScriptPath"
    }

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed."
    }
}

Write-Host "DAMA check started."

Invoke-DamaCheckScript -Label "Checking backend..." -ScriptPath ".\scripts\backend-check.ps1"
Invoke-DamaCheckScript -Label "Checking frontend..." -ScriptPath ".\scripts\frontend-check.ps1"
Invoke-DamaCheckScript -Label "Checking repo hygiene..." -ScriptPath ".\scripts\repo-hygiene-check.ps1"
Invoke-DamaCheckScript -Label "Checking security baseline..." -ScriptPath ".\scripts\security-baseline-check.ps1"
Invoke-DamaCheckScript -Label "Checking config baseline..." -ScriptPath ".\scripts\config-baseline-check.ps1"

Write-Host ""
Write-Host "DAMA check completed."
'''.strip() + "\n",
encoding="utf-8"
)

print("scripts/dama-check.ps1 hardened to stop on child check failures.")
