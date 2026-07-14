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
