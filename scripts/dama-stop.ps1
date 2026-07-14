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

$DamaProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        (
            $_.CommandLine -like "*I:\DAMA*" -or
            $_.CommandLine -like "*uvicorn src.main:app*" -or
            $_.CommandLine -like "*next dev*" -or
            $_.CommandLine -like "*dev-all.ps1*"
        ) -and
        (
            $_.Name -in @("node.exe", "python.exe", "pythonw.exe", "powershell.exe", "pwsh.exe")
        ) -and
        $_.ProcessId -ne $PID
    }

foreach ($Process in $DamaProcesses) {
    Write-Host "Stopping DAMA process: $($Process.Name) PID $($Process.ProcessId)"
    Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "DAMA local dashboard stopped."
Write-Host "Ollama was not stopped."
