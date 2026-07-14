from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""

    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


write_file(
    "scripts/open-dashboard-window.ps1",
    r'''
param(
    [Parameter(Mandatory=$true)]
    [string]$Url
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$ProfileDir = Join-Path $Root ".runtime\dama-app-window-profile"
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

function Find-Browser {
    $Candidates = @(
        (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path $env:LocalAppData "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
        (Join-Path $env:LocalAppData "Google\Chrome\Application\chrome.exe")
    )

    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate)) {
            return $Candidate
        }
    }

    $EdgeCommand = Get-Command "msedge.exe" -ErrorAction SilentlyContinue
    if ($EdgeCommand) {
        return $EdgeCommand.Source
    }

    $ChromeCommand = Get-Command "chrome.exe" -ErrorAction SilentlyContinue
    if ($ChromeCommand) {
        return $ChromeCommand.Source
    }

    return ""
}

$Browser = Find-Browser

if (-not $Browser) {
    Write-Host "Dedicated browser engine was not found. Opening default browser..."
    Start-Process $Url
    exit 0
}

Write-Host "Opening DAMA in dedicated app window..."
Write-Host "Browser: $Browser"
Write-Host "Url: $Url"

$Arguments = @(
    "--app=$Url",
    "--user-data-dir=$ProfileDir",
    "--no-first-run",
    "--disable-extensions",
    "--disable-features=Translate",
    "--window-size=1280,860"
)

Start-Process -FilePath $Browser -ArgumentList $Arguments

Write-Host "DAMA app window opened."
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

powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\open-dashboard-window.ps1" -Url $Url

Write-Host "DAMA started in dedicated app window."
    ''',
)


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

$DamaProfileMarker = ".runtime\dama-app-window-profile"

$DamaProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        (
            $_.CommandLine -like "*I:\DAMA*" -or
            $_.CommandLine -like "*uvicorn src.main:app*" -or
            $_.CommandLine -like "*next dev*" -or
            $_.CommandLine -like "*dev-all.ps1*" -or
            $_.CommandLine -like "*$DamaProfileMarker*" -or
            $_.CommandLine -like "*--app=http://localhost:3000*"
        ) -and
        (
            $_.Name -in @(
                "node.exe",
                "python.exe",
                "pythonw.exe",
                "powershell.exe",
                "pwsh.exe",
                "msedge.exe",
                "chrome.exe"
            )
        ) -and
        $_.ProcessId -ne $PID
    }

foreach ($Process in $DamaProcesses) {
    Write-Host "Stopping DAMA process/window: $($Process.Name) PID $($Process.ProcessId)"
    Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "DAMA local dashboard stopped."
Write-Host "Ollama was not stopped."
    ''',
)


append_once(
    ".gitignore",
    "# DAMA local app window runtime",
    r'''
# DAMA local app window runtime
.runtime/
    ''',
)


append_once(
    "docs/project-status.md",
    "## Hotfix AI-10.3 Completed",
    r'''
## Hotfix AI-10.3 Completed

Name:

Dedicated DAMA App Window

Added files:

- scripts/open-dashboard-window.ps1

Updated files:

- scripts/dama-start.ps1
- scripts/dama-stop.ps1
- .gitignore
- docs/project-status.md

Added behavior:

- DAMA opens in a dedicated Edge/Chrome app-style window instead of a normal browser tab.
- DAMA uses an isolated local browser profile under .runtime/dama-app-window-profile.
- Safe stop closes the dedicated DAMA window without closing the user's normal browser sessions.
- Start still restores the last saved route.
- Ollama is intentionally not stopped.
    ''',
)

print("Hotfix AI-10.3 applied successfully.")
