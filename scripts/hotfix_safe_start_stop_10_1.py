from pathlib import Path

ROOT = Path("I:/DAMA")

def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")

write_file(
    "scripts/dama-stop.ps1",
    r'''
param(
    [int]$DelaySeconds = 0,
    [switch]$SkipBackup
)

$ErrorActionPreference = "SilentlyContinue"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ($DelaySeconds -gt 0) {
    Start-Sleep -Seconds $DelaySeconds
}

Write-Host "Stopping DAMA local dashboard..."

if (-not $SkipBackup) {
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $BackupDir = Join-Path $Root "backend\backups\safe-exit\$Timestamp"
    $DataDir = Join-Path $Root "backend\data"

    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

    if (Test-Path $DataDir) {
        Copy-Item -Path (Join-Path $DataDir "*") -Destination $BackupDir -Recurse -Force
        Write-Host "Runtime backup saved to $BackupDir"
    }
}

$Ports = @(3000, 8000)

foreach ($Port in $Ports) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

    foreach ($Connection in $Connections) {
        $PidToStop = $Connection.OwningProcess

        if ($PidToStop -and $PidToStop -ne $PID) {
            Write-Host "Stopping process on port ${Port}: PID ${PidToStop}"
            Stop-Process -Id $PidToStop -Force -ErrorAction SilentlyContinue
        }
    }
}

$DamaNodePythonProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        (
            $_.CommandLine -like "*I:\DAMA*" -or
            $_.CommandLine -like "*uvicorn src.main:app*" -or
            $_.CommandLine -like "*next dev*"
        ) -and
        (
            $_.Name -in @("node.exe", "python.exe", "pythonw.exe")
        )
    }

foreach ($Process in $DamaNodePythonProcesses) {
    if ($Process.ProcessId -and $Process.ProcessId -ne $PID) {
        Write-Host "Stopping DAMA process: $($Process.Name) PID $($Process.ProcessId)"
        Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

$DamaDevShells = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        (
            $_.CommandLine -like "*dev-all.ps1*" -or
            $_.CommandLine -like "*scripts\dama-start.ps1*"
        ) -and
        (
            $_.Name -in @("powershell.exe", "pwsh.exe")
        ) -and
        $_.ProcessId -ne $PID
    }

foreach ($Shell in $DamaDevShells) {
    Write-Host "Closing DAMA PowerShell window: PID $($Shell.ProcessId)"
    Stop-Process -Id $Shell.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "DAMA local dashboard stopped."
Write-Host "Ollama was not stopped."
    ''',
)

write_file(
    "scripts/dama-start.ps1",
    r'''
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

Start-Process $Url

Write-Host "DAMA started. Browser opened at $Url"
    ''',
)

print("Safe start/stop scripts patched.")
