param(
    [switch]$CleanPorts
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ($CleanPorts) {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\dama-stop.ps1" -SkipBackup
    Start-Sleep -Seconds 1
}

$SessionPath = Join-Path $Root "backend\data\operator_session.json"
$LastRoute = "/"

if (Test-Path $SessionPath) {
    try {
        $Session = Get-Content -LiteralPath $SessionPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($Session.last_route) {
            $LastRoute = [string]$Session.last_route
        }
    } catch {
        $LastRoute = "/"
    }
}

if (-not $LastRoute.StartsWith("/")) {
    $LastRoute = "/"
}

$Url = "http://localhost:3000$LastRoute"

Write-Host "Starting DAMA local dashboard..."
Write-Host "Last route: $LastRoute"

Start-Process powershell.exe -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    "`"$Root\scripts\dev-all.ps1`""
)

Start-Sleep -Seconds 6

powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\open-dashboard-window.ps1" -Url $Url

Write-Host "DAMA started in dedicated app window."
