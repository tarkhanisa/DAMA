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
    "backend/src/services/operator_session_service.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import shutil
import subprocess


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_DIR = BACKEND_ROOT / "data"
SESSION_PATH = DATA_DIR / "operator_session.json"
BACKUP_ROOT = BACKEND_ROOT / "backups" / "safe-exit"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_session_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SESSION_PATH.exists():
        SESSION_PATH.write_text(
            json.dumps(
                {
                    "last_route": "/",
                    "updated_at": utc_now(),
                    "history": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def read_operator_session() -> dict[str, Any]:
    ensure_session_store()

    try:
        payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {}

    return payload if isinstance(payload, dict) else {}


def write_operator_session(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_session_store()
    payload["updated_at"] = utc_now()

    SESSION_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def normalize_route(route: Any) -> str:
    text = str(route or "/").strip()

    if not text.startswith("/"):
        text = "/" + text

    if text in {"/other/exit", "/exit"}:
        return "/"

    return text


def update_last_route(route: Any) -> dict[str, Any]:
    session = read_operator_session()
    next_route = normalize_route(route)

    session["last_route"] = next_route
    session["last_route_updated_at"] = utc_now()

    history = session.get("history")
    if not isinstance(history, list):
        history = []

    history.insert(
        0,
        {
            "event": "route_updated",
            "route": next_route,
            "at": utc_now(),
        },
    )

    session["history"] = history[:100]

    return write_operator_session(session)


def backup_runtime_data() -> str:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup_dir = BACKUP_ROOT / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            target = backup_dir / item.name

            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    return str(backup_dir)


def schedule_dama_shutdown(delay_seconds: int = 2) -> None:
    script_path = PROJECT_ROOT / "scripts" / "dama-stop.ps1"

    if not script_path.exists():
        return

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-DelaySeconds",
        str(max(0, delay_seconds)),
        "-SkipBackup",
    ]

    creationflags = 0

    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def safe_exit(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = payload or {}
    last_route = normalize_route(request.get("last_route") or "/")
    make_backup = bool(request.get("backup", True))
    shutdown = bool(request.get("shutdown", True))

    session = update_last_route(last_route)

    backup_path = ""

    if make_backup:
        backup_path = backup_runtime_data()

    session["last_safe_exit_at"] = utc_now()
    session["last_safe_exit_route"] = last_route
    session["last_safe_exit_backup_path"] = backup_path
    session = write_operator_session(session)

    if shutdown:
        schedule_dama_shutdown(delay_seconds=2)

    return {
        "ok": True,
        "last_route": last_route,
        "backup_path": backup_path,
        "shutdown_scheduled": shutdown,
        "message": (
            "خروج امن ثبت شد. تا چند ثانیه دیگر سرورهای DAMA بسته می‌شوند."
            if shutdown
            else "خروج امن ثبت شد."
        ),
        "session": session,
    }
    ''',
)


api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "operator_session_service" not in api:
    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\nfrom src.services.operator_session_service import (\n    read_operator_session,\n    safe_exit,\n    update_last_route,\n)\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/operator/session")' not in api:
    api += r'''


@router.get("/operator/session")
def api_get_operator_session() -> dict[str, Any]:
    return read_operator_session()


@router.post("/operator/session/route")
def api_update_operator_route(payload: dict[str, Any]) -> dict[str, Any]:
    return update_last_route(payload.get("last_route"))


@router.post("/operator/session/safe-exit")
def api_operator_safe_exit(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return safe_exit(payload)
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with operator session endpoints.")


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
            Write-Host "Stopping process on port $Port: PID $PidToStop"
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
            $_.CommandLine -like "*next dev*"
        ) -and
        (
            $_.Name -in @("node.exe", "python.exe", "pythonw.exe")
        )
    }

foreach ($Process in $DamaProcesses) {
    if ($Process.ProcessId -and $Process.ProcessId -ne $PID) {
        Write-Host "Stopping DAMA process: $($Process.Name) PID $($Process.ProcessId)"
        Stop-Process -Id $Process.ProcessId -Force -ErrorAction SilentlyContinue
    }
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
    "-NoExit",
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


write_file(
    "backend/tests/smoke_test_operator_session.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    route_response = client.post(
        "/publishing/operator/session/route",
        json={"last_route": "/publishing"},
    )
    assert route_response.status_code == 200, route_response.text
    assert route_response.json()["last_route"] == "/publishing"

    session_response = client.get("/publishing/operator/session")
    assert session_response.status_code == 200, session_response.text
    assert session_response.json()["last_route"] == "/publishing"

    exit_response = client.post(
        "/publishing/operator/session/safe-exit",
        json={
            "last_route": "/produce/video",
            "backup": False,
            "shutdown": False,
        },
    )
    assert exit_response.status_code == 200, exit_response.text
    payload = exit_response.json()
    assert payload["ok"] is True
    assert payload["last_route"] == "/produce/video"

    print("Operator session smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


backend_check = ROOT / "scripts/backend-check.ps1"
backend_text = backend_check.read_text(encoding="utf-8")

if "smoke_test_operator_session.py" not in backend_text:
    backend_text = backend_text.rstrip() + r'''

$OperatorSessionSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_operator_session.py"
$OperatorSessionPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $OperatorSessionSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_operator_session.py..."
    & $OperatorSessionPython $OperatorSessionSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_operator_session.py"
    }
}
''' + "\n"

    backend_check.write_text(backend_text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


write_file(
    "frontend/src/components/last-session-card.tsx",
    r'''
"use client";

import { useEffect, useState } from "react";

function routeTitle(route: string): string {
  if (route.startsWith("/publishing")) {
    return "ادامه انتشار";
  }

  if (route.startsWith("/produce/video")) {
    return "ادامه تولید ویدیو";
  }

  if (route.startsWith("/produce")) {
    return "ادامه تولید";
  }

  if (route.startsWith("/other")) {
    return "ادامه سایر";
  }

  return "ادامه از آخرین صفحه";
}

export function LastSessionCard() {
  const [lastRoute, setLastRoute] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("dama:last-route") ?? "";

    if (stored && stored !== "/" && stored !== "/other/exit") {
      setLastRoute(stored);
    }
  }, []);

  if (!lastRoute) {
    return null;
  }

  return (
    <section className="last-session-card">
      <div>
        <p className="eyebrow">ادامه کار قبلی</p>
        <h2>{routeTitle(lastRoute)}</h2>
        <p>آخرین صفحه‌ای که داخل پنل باز کرده بودی ذخیره شده است.</p>
      </div>

      <a href={lastRoute}>رفتن به آخرین صفحه</a>
    </section>
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
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
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


# Patch app-nav to remember last route.
app_nav_path = ROOT / "frontend/src/components/app-nav.tsx"
app_nav = app_nav_path.read_text(encoding="utf-8")

if "useEffect" not in app_nav:
    app_nav = app_nav.replace(
        'import { usePathname } from "next/navigation";',
        'import { usePathname } from "next/navigation";\nimport { useEffect } from "react";',
    )

if "dama:last-route" not in app_nav:
    app_nav = app_nav.replace(
        "  const pathname = usePathname();",
        r'''  const pathname = usePathname();

  useEffect(() => {
    if (pathname && pathname !== "/other/exit") {
      window.localStorage.setItem("dama:last-route", pathname);

      fetch("http://127.0.0.1:8000/publishing/operator/session/route", {
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
  }, [pathname]);''',
    )

app_nav_path.write_text(app_nav, encoding="utf-8")
print("Patched app-nav with route memory.")


# Patch home page with last session card.
home_path = ROOT / "frontend/src/app/page.tsx"
home = home_path.read_text(encoding="utf-8")

if "LastSessionCard" not in home:
    home = home.replace(
        'import { PageHeader } from "../components/page-header";',
        'import { LastSessionCard } from "../components/last-session-card";\nimport { PageHeader } from "../components/page-header";',
    )

    home = home.replace(
        '<section className="simple-route-hint">',
        '<LastSessionCard />\n\n      <section className="simple-route-hint">',
        1,
    )

home_path.write_text(home, encoding="utf-8")
print("Patched home page with last session card.")


write_file(
    "frontend/src/app/other/exit/page.tsx",
    r'''
import { PageHeader } from "../../../components/page-header";
import { SafeExitAction } from "../../../components/safe-exit-action";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function SafeExitPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="خروج امن"
        title="بستن امن داشبورد DAMA"
        lead="آخرین صفحه ذخیره می‌شود، از داده‌های runtime پشتیبان گرفته می‌شود و سرورهای محلی داشبورد بسته می‌شوند."
      >
        <div className="actions">
          <a href="/">بازگشت به داشبورد</a>
          <a href="/other">سایر</a>
        </div>
      </PageHeader>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">عملیات</p>
            <h2>خروج امن</h2>
          </div>

          <p className="muted-note">
            این کار Ollama را نمی‌بندد. فقط backend و frontend مربوط به DAMA را متوقف می‌کند.
            داده‌های کاری که داخل فایل‌های runtime ذخیره شده‌اند از بین نمی‌روند.
          </p>

          <SafeExitAction apiBaseUrl={API_BASE_URL} />
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">دفعه بعد</p>
            <h2>شروع از آخرین صفحه</h2>
          </div>

          <ol className="simple-steps">
            <li>برای شروع بعدی از اسکریپت start استفاده کن.</li>
            <li>مرورگر به آخرین صفحه ذخیره‌شده باز می‌شود.</li>
            <li>اگر مرورگر مستقیم صفحه اصلی را باز کرد، کارت «ادامه کار قبلی» را می‌بینی.</li>
          </ol>

          <pre className="json-block">cd I:\DAMA
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama-start.ps1 -CleanPorts</pre>
        </section>
      </section>
    </main>
  );
}
    ''',
)


# Patch Other page with safe exit link.
other_path = ROOT / "frontend/src/app/other/page.tsx"
other = other_path.read_text(encoding="utf-8")

if "/other/exit" not in other:
    other = other.replace(
        '''{
        href: "/advanced/cleanup",
        title: "پاک‌سازی داده‌های تستی",
        description: "حذف امن داده‌های smoke/test با backup."
      },''',
        '''{
        href: "/advanced/cleanup",
        title: "پاک‌سازی داده‌های تستی",
        description: "حذف امن داده‌های smoke/test با backup."
      },
      {
        href: "/other/exit",
        title: "خروج امن",
        description: "ذخیره آخرین صفحه، backup و بستن سرورهای محلی DAMA."
      },''',
    )

other_path.write_text(other, encoding="utf-8")
print("Patched other page with safe exit link.")


append_once(
    "frontend/src/app/globals.css",
    "/* Safe start and safe exit */",
    r'''
/* Safe start and safe exit */
.last-session-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: center;
  margin: 1rem 0 1.25rem;
  padding: 1.1rem 1.25rem;
  border: 1px solid rgba(35, 74, 112, 0.28);
  border-radius: 1.35rem;
  background:
    radial-gradient(circle at top right, rgba(35, 74, 112, 0.12), transparent 32%),
    rgba(255, 255, 255, 0.88);
  box-shadow: var(--shadow);
}

.last-session-card h2 {
  margin: 0.2rem 0 0.4rem;
}

.last-session-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.last-session-card a,
.safe-exit-action button {
  display: inline-flex;
  min-height: 2.8rem;
  align-items: center;
  justify-content: center;
  padding: 0 1rem;
  border: 0;
  border-radius: 999px;
  background: var(--text);
  color: white;
  text-decoration: none;
  font-weight: 900;
  cursor: pointer;
}

.safe-exit-action {
  display: grid;
  gap: 0.8rem;
}

.safe-exit-action button:disabled {
  opacity: 0.7;
  cursor: wait;
}

@media (max-width: 720px) {
  .last-session-card {
    grid-template-columns: 1fr;
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
    ".\frontend\src\components\last-session-card.tsx",
    ".\frontend\src\components\safe-exit-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\other\page.tsx",
    ".\frontend\src\app\other\exit\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$AppNav = Read-TextFile ".\frontend\src\components\app-nav.tsx"
$HomePage = Read-TextFile ".\frontend\src\app\page.tsx"
$OtherPage = Read-TextFile ".\frontend\src\app\other\page.tsx"
$ExitPage = Read-TextFile ".\frontend\src\app\other\exit\page.tsx"
$SafeExitAction = Read-TextFile ".\frontend\src\components\safe-exit-action.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($AppNav -notmatch "dama:last-route") {
    throw "App nav is not remembering last route."
}

if ($HomePage -notmatch "LastSessionCard") {
    throw "Home page is missing last session card."
}

if ($OtherPage -notmatch "/other/exit") {
    throw "Other page does not link to safe exit."
}

if ($ExitPage -notmatch "SafeExitAction") {
    throw "Safe exit page is missing safe exit action."
}

if ($SafeExitAction -notmatch "/publishing/operator/session/safe-exit") {
    throw "Safe exit action does not call backend safe exit endpoint."
}

if ($Styles -notmatch "Safe start and safe exit") {
    throw "Global styles missing safe exit marker."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-10 Completed",
    r'''
## Release Pack AI-10 Completed

Name:

Safe Start / Safe Exit / Restore Last Page

Added files:

- backend/src/services/operator_session_service.py
- backend/tests/smoke_test_operator_session.py
- scripts/dama-start.ps1
- scripts/dama-stop.ps1
- frontend/src/components/last-session-card.tsx
- frontend/src/components/safe-exit-action.tsx
- frontend/src/app/other/exit/page.tsx

Updated files:

- backend/src/api/publishing.py
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- frontend/src/components/app-nav.tsx
- frontend/src/app/page.tsx
- frontend/src/app/other/page.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- app remembers the last visited route
- home page shows a continue-last-page card
- safe exit page saves last route
- safe exit creates runtime data backup
- safe exit schedules local dashboard shutdown
- stop script closes frontend/backend local processes on ports 3000 and 8000
- start script opens the dashboard at the last saved route
- Ollama is intentionally not stopped

Recommended daily usage:

Start:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama-start.ps1 -CleanPorts

Stop:

Use /other/exit in the UI or run:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama-stop.ps1
    ''',
)


print("Release Pack AI-10 applied successfully.")
