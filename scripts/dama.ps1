param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("check", "status", "ship", "backup", "help")]
    [string] $Command,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Rest
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Message = ($Rest -join " ").Trim()

function Show-Help {
    Write-Host ""
    Write-Host "DAMA Autopilot Runner"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  check         Run backend and frontend readiness checks"
    Write-Host "  status        Show Git status and recent commits"
    Write-Host "  ship MESSAGE  Run checks, stage all changes, commit, and push"
    Write-Host "  backup        Create local database backup through backend service"
    Write-Host "  help          Show this help"
    Write-Host ""
}

switch ($Command) {
    "help" {
        Show-Help
    }

    "status" {
        Write-Host "Git status:"
        git status --short

        Write-Host ""
        Write-Host "Recent commits:"
        git log --oneline -8
    }

    "check" {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\dama-check.ps1"
    }

    "ship" {
        if (-not $Message) {
            throw "Commit message is required."
        }

        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\dama-ship.ps1" -Message $Message
    }

    "backup" {
        Push-Location ".\backend"
        try {
            & ".\.venv\Scripts\python.exe" -c "from fastapi.testclient import TestClient; from src.main import app; client=TestClient(app); r=client.post('/maintenance/database/backup'); print(r.status_code); print(r.json())"
        }
        finally {
            Pop-Location
        }
    }
}
