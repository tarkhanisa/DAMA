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
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/produce", label: "تولید" },
  { href: "/publishing", label: "انتشار" },
  { href: "/other", label: "سایر" }
];

function showClosedScreen() {
  document.documentElement.innerHTML = `
    <html lang="fa" dir="rtl">
      <head>
        <title>DAMA بسته شد</title>
        <style>
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0f172a;
            color: #fff;
          }
          main {
            width: min(560px, calc(100vw - 32px));
            padding: 32px;
            border: 1px solid rgba(255,255,255,.16);
            border-radius: 24px;
            background: rgba(255,255,255,.08);
            text-align: center;
          }
          h1 { margin: 0 0 12px; font-size: 28px; }
          p { margin: 0; line-height: 2; color: rgba(255,255,255,.76); }
        </style>
      </head>
      <body>
        <main>
          <h1>خروج امن انجام شد</h1>
          <p>سرورهای محلی DAMA در حال بسته‌شدن هستند. اگر این تب خودکار بسته نشد، می‌توانی آن را دستی ببندی.</p>
        </main>
      </body>
    </html>
  `;
}

export function AppNav() {
  const pathname = usePathname();
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (pathname && pathname !== "/other/exit") {
      window.localStorage.setItem("dama:last-route", pathname);

      fetch(`${API_BASE_URL}/publishing/operator/session/route`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          last_route: pathname
        })
      }).catch(() => {
        // Local backend may be offline while frontend renders.
      });
    }
  }, [pathname]);

  async function handleSafeExit() {
    const confirmed = window.confirm(
      "خروج امن انجام شود؟ آخرین صفحه ذخیره می‌شود، backup گرفته می‌شود و سرورهای DAMA بسته می‌شوند."
    );

    if (!confirmed) {
      return;
    }

    const lastRoute =
      window.localStorage.getItem("dama:last-route") ||
      pathname ||
      "/";

    setIsExiting(true);

    try {
      await fetch(`${API_BASE_URL}/publishing/operator/session/safe-exit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          last_route: lastRoute,
          backup: true,
          shutdown: true
        })
      });
    } catch {
      // Even if the response is interrupted by shutdown, continue closing the UI.
    }

    window.setTimeout(() => {
      try {
        window.open("", "_self");
        window.close();
      } catch {
        // Browser may block closing tabs it did not open by script.
      }

      window.setTimeout(() => {
        showClosedScreen();
      }, 500);
    }, 900);
  }

  return (
    <div className="app-nav-shell">
      <nav className="app-nav" aria-label="ناوبری اصلی DAMA">
        {navItems.map((item) => {
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={isActive ? "active" : undefined}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <button
        className="safe-exit-top-button"
        type="button"
        onClick={handleSafeExit}
        disabled={isExiting}
      >
        {isExiting ? "در حال خروج..." : "خروج امن"}
      </button>
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/components/safe-exit-action.tsx",
    r'''
"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type SafeExitActionProps = {
  apiBaseUrl: string;
};

function showClosedScreen() {
  document.documentElement.innerHTML = `
    <html lang="fa" dir="rtl">
      <head>
        <title>DAMA بسته شد</title>
        <style>
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0f172a;
            color: #fff;
          }
          main {
            width: min(560px, calc(100vw - 32px));
            padding: 32px;
            border: 1px solid rgba(255,255,255,.16);
            border-radius: 24px;
            background: rgba(255,255,255,.08);
            text-align: center;
          }
          h1 { margin: 0 0 12px; font-size: 28px; }
          p { margin: 0; line-height: 2; color: rgba(255,255,255,.76); }
        </style>
      </head>
      <body>
        <main>
          <h1>خروج امن انجام شد</h1>
          <p>اگر این تب خودکار بسته نشد، می‌توانی آن را دستی ببندی.</p>
        </main>
      </body>
    </html>
  `;
}

export function SafeExitAction({ apiBaseUrl }: SafeExitActionProps) {
  const [isExiting, setIsExiting] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSafeExit() {
    const lastRoute = window.localStorage.getItem("dama:last-route") || "/";
    setIsExiting(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/operator/session/safe-exit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          last_route: lastRoute,
          backup: true,
          shutdown: true
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage(payload.message ?? "خروج امن ثبت شد. تا چند ثانیه دیگر DAMA بسته می‌شود.");

      window.setTimeout(() => {
        try {
          window.open("", "_self");
          window.close();
        } catch {
          // Browser may block closing tabs it did not open by script.
        }

        window.setTimeout(() => {
          showClosedScreen();
        }, 500);
      }, 900);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));

      window.setTimeout(() => {
        showClosedScreen();
      }, 1200);
    } finally {
      window.setTimeout(() => setIsExiting(false), 3000);
    }
  }

  return (
    <div className="safe-exit-action">
      <button type="button" onClick={handleSafeExit} disabled={isExiting}>
        {isExiting ? "در حال خروج امن..." : "خروج امن و بستن داشبورد"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
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
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Sticky red safe exit button */",
    r'''
/* Sticky red safe exit button */
.app-nav-shell {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 80;
  padding: 0.75rem 1rem;
  backdrop-filter: blur(16px);
  background: rgba(248, 250, 252, 0.82);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.app-nav-shell .app-nav {
  position: static;
  top: auto;
  z-index: auto;
  padding: 0;
  border-bottom: 0;
  background: transparent;
  backdrop-filter: none;
}

.safe-exit-top-button {
  display: inline-flex;
  min-height: 2.45rem;
  align-items: center;
  justify-content: center;
  padding: 0 1rem;
  border: 0;
  border-radius: 999px;
  background: #b42318;
  color: #fff;
  font-weight: 950;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(180, 35, 24, 0.24);
  white-space: nowrap;
}

.safe-exit-top-button:hover {
  background: #912018;
}

.safe-exit-top-button:disabled {
  opacity: 0.72;
  cursor: wait;
}

@media (max-width: 720px) {
  .app-nav-shell {
    align-items: stretch;
    flex-direction: column;
  }

  .safe-exit-top-button {
    width: 100%;
  }
}
    ''',
)


write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path -LiteralPath ".\frontend\node_modules")) {
    throw "frontend/node_modules not found. Run npm install in frontend first."
}

Write-Host "node_modules found. Running frontend typecheck..."

Push-Location ".\frontend"
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Frontend typecheck failed."
}
Pop-Location

$RequiredFiles = @(
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\safe-exit-action.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$SafeExitAction = Read-TextFile ".\frontend\src\components\safe-exit-action.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($AppNav -notmatch "safe-exit-top-button") {
    throw "App nav is missing sticky safe exit button."
}

if ($AppNav -notmatch "/publishing/operator/session/safe-exit") {
    throw "App nav safe exit button does not call backend safe exit endpoint."
}

if ($AppNav -notmatch "window.close") {
    throw "App nav safe exit does not attempt to close the browser tab."
}

if ($SafeExitAction -notmatch "window.close") {
    throw "Safe exit page does not attempt to close the browser tab."
}

if ($Styles -notmatch "Sticky red safe exit button") {
    throw "Global styles missing sticky red safe exit marker."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


with open(ROOT / "docs/project-status.md", "a", encoding="utf-8") as f:
    f.write(
        "\n\n## Hotfix AI-10.2 Completed\n\n"
        "Name:\n\n"
        "Sticky Red Safe Exit Button\n\n"
        "Added behavior:\n\n"
        "- Safe Exit is always visible in the sticky top navigation.\n"
        "- Safe Exit button is red and prominent.\n"
        "- Safe Exit saves last route, creates backup and schedules backend/frontend shutdown.\n"
        "- Browser tab close is attempted with window.close().\n"
        "- If the browser blocks tab closing, a closed-screen fallback is shown.\n"
        "- dama-stop.ps1 was hardened to stop DAMA node/python/powershell processes while keeping Ollama alive.\n"
    )

print("Hotfix AI-10.2 applied successfully.")
