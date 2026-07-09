from pathlib import Path
import re

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


def patch_main() -> None:
    target = ROOT / "backend/src/main.py"
    text = target.read_text(encoding="utf-8")

    if "from src.api.runtime import router as runtime_router" not in text:
        lines = text.splitlines()
        insert_at = 0

        for index, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = index + 1

        lines.insert(insert_at, "from src.api.runtime import router as runtime_router")
        text = "\n".join(lines)

    if "app.include_router(runtime_router)" not in text:
        text = text.rstrip() + "\n\napp.include_router(runtime_router)\n"

    target.write_text(text.strip() + "\n", encoding="utf-8")
    print("Patched backend/src/main.py")


def patch_api_init() -> None:
    target = ROOT / "backend/src/api/__init__.py"
    text = target.read_text(encoding="utf-8") if target.exists() else ""

    if "runtime" not in text:
        text = text.rstrip() + "\nfrom . import runtime\n"

    target.write_text(text.strip() + "\n", encoding="utf-8")
    print("Patched backend/src/api/__init__.py")


def patch_frontend_nav() -> None:
    target = ROOT / "frontend/src/components/app-nav.tsx"
    if not target.exists():
        print("Skipped app-nav patch; file not found.")
        return

    text = target.read_text(encoding="utf-8")

    if "/runtime" in text:
        print("Skipped app-nav patch; runtime already exists.")
        return

    inserted = False

    patterns = [
        ('{ href: "/operations", label: "Operations" }',
         '{ href: "/runtime", label: "Runtime" },\n  { href: "/operations", label: "Operations" }'),
        ('{ href: "/operations", label: "Operations",',
         '{ href: "/runtime", label: "Runtime" },\n  { href: "/operations", label: "Operations",'),
        ('href="/operations"',
         'href="/runtime">Runtime</a>\n        <a href="/operations"')
    ]

    for old, new in patterns:
        if old in text:
            text = text.replace(old, new, 1)
            inserted = True
            break

    if not inserted:
        # Safe fallback: add a visible link near the end of the nav if a nav element exists.
        text = text.replace("</nav>", '  <a href="/runtime">Runtime</a>\n</nav>', 1)
        inserted = "/runtime" in text

    target.write_text(text, encoding="utf-8")
    print("Patched frontend nav." if inserted else "Could not patch frontend nav automatically.")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if ".\\frontend\\src\\app\\runtime\\page.tsx" not in text:
        marker = '".\\frontend\\src\\app\\operations\\page.tsx",'
        if marker in text:
            text = text.replace(
                marker,
                marker + '\n    ".\\frontend\\src\\app\\runtime\\page.tsx",',
                1
            )

    if "Runtime page does not include runtime health fetch." not in text:
        insert = r'''
$RuntimePage = Read-TextFile ".\frontend\src\app\runtime\page.tsx"

if ($RuntimePage -notmatch "/runtime/health") {
    throw "Runtime page does not include runtime health fetch."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            insert + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


def patch_backend_check() -> None:
    target = ROOT / "scripts/backend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "smoke_test_runtime.py" in text:
        print("Skipped backend-check patch; runtime smoke already exists.")
        return

    # Prefer adding to existing smoke test list if smoke_test_search exists.
    if '"./backend/tests/smoke_test_search.py"' in text:
        text = text.replace(
            '"./backend/tests/smoke_test_search.py"',
            '"./backend/tests/smoke_test_search.py",\n    "./backend/tests/smoke_test_runtime.py"',
            1,
        )
    elif '".\\backend\\tests\\smoke_test_search.py"' in text:
        text = text.replace(
            '".\\backend\\tests\\smoke_test_search.py"',
            '".\\backend\\tests\\smoke_test_search.py",\n    ".\\backend\\tests\\smoke_test_runtime.py"',
            1,
        )
    else:
        # Robust fallback appended at the end.
        text = text.rstrip() + r'''

$RuntimeSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_runtime.py"
$RuntimePython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $RuntimeSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_runtime.py..."
    & $RuntimePython $RuntimeSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_runtime.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


write_file(
    "backend/src/api/runtime.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter


router = APIRouter(prefix="/runtime", tags=["runtime"])

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status_value(ok: bool, warning: bool = False) -> str:
    if ok:
        return "ok"
    if warning:
        return "warning"
    return "error"


def path_probe(label: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    is_directory = path.is_dir() if exists else False
    check_target = path if exists else path.parent
    writable = os.access(check_target, os.W_OK) if check_target.exists() else False

    return {
        "label": label,
        "path": str(path),
        "exists": exists,
        "is_directory": is_directory,
        "writable": writable,
        "status": status_value(exists and is_directory and writable, warning=True),
    }


def tcp_probe(host: str, port: int, timeout_seconds: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def ollama_probe() -> dict[str, Any]:
    base_url = os.getenv("DAMA_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    tags_url = f"{base_url}/api/tags"

    try:
        request = Request(tags_url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=1.0) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            models = payload.get("models", [])

        return {
            "status": "ok",
            "base_url": base_url,
            "reachable": True,
            "model_count": len(models),
            "models": [
                model.get("name")
                for model in models
                if isinstance(model, dict) and model.get("name")
            ][:20],
        }
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "status": "warning",
            "base_url": base_url,
            "reachable": False,
            "model_count": 0,
            "models": [],
            "message": str(exc),
        }


def safe_config() -> dict[str, Any]:
    public_keys = [
        "DAMA_ENV",
        "DAMA_DEBUG",
        "DAMA_API_BASE_URL",
        "DAMA_FRONTEND_ORIGIN",
        "DAMA_AI_PROVIDER",
        "DAMA_OLLAMA_BASE_URL",
        "DAMA_OLLAMA_DEFAULT_MODEL",
    ]

    return {
        "environment": {
            key: os.getenv(key)
            for key in public_keys
            if os.getenv(key) is not None
        },
        "has_next_public_api_url": os.getenv("NEXT_PUBLIC_DAMA_API_BASE_URL") is not None,
        "secrets_redacted": True,
    }


@router.get("/health")
def runtime_health() -> dict[str, Any]:
    data_dir = Path(os.getenv("DAMA_DATA_DIR", str(BACKEND_ROOT / "data")))
    exports_dir = Path(os.getenv("DAMA_EXPORTS_DIR", str(BACKEND_ROOT / "exports")))
    backups_dir = Path(os.getenv("DAMA_BACKUPS_DIR", str(BACKEND_ROOT / "backups")))

    storage = [
        path_probe("data", data_dir),
        path_probe("exports", exports_dir),
        path_probe("backups", backups_dir),
    ]

    storage_required_ok = all(item["exists"] and item["is_directory"] for item in storage)
    storage_writable = all(item["writable"] for item in storage)

    ollama = ollama_probe()

    overall = "ok"
    if not storage_required_ok:
        overall = "warning"
    if storage_required_ok and not storage_writable:
        overall = "warning"

    return {
        "ok": overall == "ok",
        "status": overall,
        "checked_at": utc_now(),
        "backend": {
            "status": "ok",
            "project_root": str(PROJECT_ROOT),
            "backend_root": str(BACKEND_ROOT),
            "runtime": "fastapi",
        },
        "storage": storage,
        "ollama": ollama,
        "config": safe_config(),
        "operator_notes": [
            "Ollama unreachable is warning-level for UI readiness, not a backend failure.",
            "Runtime paths should exist before real production deployment.",
            "Secrets are intentionally not returned by this endpoint.",
        ],
    }
    ''',
)


write_file(
    "backend/tests/smoke_test_runtime.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    response = client.get("/runtime/health")
    assert response.status_code == 200, response.text

    payload = response.json()

    assert "ok" in payload
    assert "status" in payload
    assert "backend" in payload
    assert "storage" in payload
    assert "ollama" in payload
    assert "config" in payload

    assert isinstance(payload["storage"], list)
    assert payload["backend"]["runtime"] == "fastapi"

    print("Runtime smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/app/runtime/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

type RuntimeStorageItem = {
  label: string;
  path: string;
  exists: boolean;
  is_directory: boolean;
  writable: boolean;
  status: string;
};

type RuntimeHealth = {
  ok: boolean;
  status: string;
  checked_at: string;
  backend: {
    status: string;
    project_root: string;
    backend_root: string;
    runtime: string;
  };
  storage: RuntimeStorageItem[];
  ollama: {
    status: string;
    base_url: string;
    reachable: boolean;
    model_count: number;
    models: string[];
    message?: string;
  };
  config: {
    environment: Record<string, string>;
    has_next_public_api_url: boolean;
    secrets_redacted: boolean;
  };
  operator_notes: string[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

function fallbackHealth(message: string): RuntimeHealth {
  return {
    ok: false,
    status: "warning",
    checked_at: new Date().toISOString(),
    backend: {
      status: "warning",
      project_root: "unknown",
      backend_root: "unknown",
      runtime: "fastapi"
    },
    storage: [],
    ollama: {
      status: "unknown",
      base_url: "unknown",
      reachable: false,
      model_count: 0,
      models: [],
      message
    },
    config: {
      environment: {},
      has_next_public_api_url: Boolean(process.env.NEXT_PUBLIC_DAMA_API_BASE_URL),
      secrets_redacted: true
    },
    operator_notes: [
      "Frontend could not reach the backend runtime health endpoint.",
      "Start the backend first, then refresh this page."
    ]
  };
}

async function loadRuntimeHealth(): Promise<RuntimeHealth> {
  try {
    const response = await fetch(`${API_BASE_URL}/runtime/health`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return fallbackHealth(`Backend responded with HTTP ${response.status}.`);
    }

    return (await response.json()) as RuntimeHealth;
  } catch (error) {
    return fallbackHealth(error instanceof Error ? error.message : "Unknown error");
  }
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`status-badge status-${status}`}>{status}</span>;
}

export default async function RuntimePage() {
  const health = await loadRuntimeHealth();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Runtime"
        title="Operator runtime health"
        lead="A safe read-only view of backend availability, Ollama reachability, local storage paths, and public configuration."
      >
        <div className="actions">
          <a href={`${API_BASE_URL}/runtime/health`}>Raw Runtime JSON</a>
          <a href={`${API_BASE_URL}/docs`}>API Docs</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Overall" value={health.status} helper="Runtime status" />
        <StatCard
          label="Backend"
          value={health.backend.status}
          helper={health.backend.runtime}
        />
        <StatCard
          label="Ollama"
          value={health.ollama.reachable ? "reachable" : "not reachable"}
          helper={health.ollama.base_url}
        />
        <StatCard
          label="Models"
          value={health.ollama.model_count}
          helper="Local Ollama model count"
        />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Backend</p>
            <h2>Backend runtime</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>Status</strong>
              <StatusBadge status={health.backend.status} />
            </div>
            <div>
              <strong>Project root</strong>
              <span>{health.backend.project_root}</span>
            </div>
            <div>
              <strong>Backend root</strong>
              <span>{health.backend.backend_root}</span>
            </div>
            <div>
              <strong>Checked at</strong>
              <span>{health.checked_at}</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Ollama</p>
            <h2>Local model service</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>Status</strong>
              <StatusBadge status={health.ollama.status} />
            </div>
            <div>
              <strong>Reachable</strong>
              <span>{health.ollama.reachable ? "Yes" : "No"}</span>
            </div>
            <div>
              <strong>Base URL</strong>
              <span>{health.ollama.base_url}</span>
            </div>
            <div>
              <strong>Models</strong>
              <span>
                {health.ollama.models.length > 0
                  ? health.ollama.models.join(", ")
                  : "No models listed"}
              </span>
            </div>
          </div>

          {health.ollama.message ? (
            <p className="muted-note">{health.ollama.message}</p>
          ) : null}
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Storage</p>
          <h2>Local runtime paths</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>Label</th>
                <th>Status</th>
                <th>Exists</th>
                <th>Writable</th>
                <th>Path</th>
              </tr>
            </thead>
            <tbody>
              {health.storage.length > 0 ? (
                health.storage.map((item) => (
                  <tr key={item.label}>
                    <td>{item.label}</td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>{item.exists ? "Yes" : "No"}</td>
                    <td>{item.writable ? "Yes" : "No"}</td>
                    <td>{item.path}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>No storage data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Config</p>
            <h2>Public configuration</h2>
          </div>

          <pre className="json-block">
            {JSON.stringify(health.config, null, 2)}
          </pre>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Operator Notes</p>
            <h2>Read-only safety notes</h2>
          </div>

          <ul className="note-list">
            {health.operator_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Runtime health */",
    r'''
/* Runtime health */
.health-list {
  display: grid;
  gap: 0.9rem;
}

.health-list > div {
  display: grid;
  gap: 0.35rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.health-list strong {
  color: var(--text);
}

.health-list span {
  color: var(--muted);
  word-break: break-word;
}

.status-badge {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  border-radius: 999px;
  padding: 0.25rem 0.65rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  border: 1px solid var(--border);
}

.status-ok {
  background: rgba(49, 145, 87, 0.12);
}

.status-warning,
.status-unknown {
  background: rgba(220, 151, 49, 0.14);
}

.status-error {
  background: rgba(200, 70, 70, 0.14);
}

.responsive-table {
  width: 100%;
  overflow-x: auto;
}

.responsive-table table {
  width: 100%;
  border-collapse: collapse;
}

.responsive-table th,
.responsive-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}

.json-block {
  white-space: pre-wrap;
  word-break: break-word;
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.6);
}

.note-list {
  display: grid;
  gap: 0.75rem;
  color: var(--muted);
}

.muted-note {
  color: var(--muted);
  margin-top: 1rem;
}
    ''',
)


write_file(
    "docs/runtime-health.md",
    r'''
# DAMA Runtime Health

Release Pack T adds a read-only runtime health endpoint and frontend page.

## Backend Endpoint

    GET /runtime/health

Returns:

- backend runtime status
- local storage path status
- Ollama reachability
- safe public config
- operator notes

## Frontend Page

    http://localhost:3000/runtime

## Safety

This endpoint is read-only.

It does not:

- expose secrets
- mutate database state
- create/delete files
- run generation
- execute batch jobs

## Ollama Status

Ollama unreachable is warning-level during local development.

It means:

- backend can run
- frontend can load
- generation may fail until Ollama is started

## Smoke Test

Run:

    .\backend\.venv\Scripts\python.exe .\backend\tests\smoke_test_runtime.py

Or full check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check
    ''',
)


append_once(
    "README.md",
    "## DAMA Runtime Health",
    r'''
## DAMA Runtime Health

Backend runtime health:

    http://127.0.0.1:8000/runtime/health

Frontend runtime dashboard:

    http://localhost:3000/runtime

This dashboard is read-only and safe for operator diagnostics.
    ''',
)


append_once(
    "docs/production-readiness.md",
    "## Runtime Health",
    r'''
## Runtime Health

Release Pack T adds:

- backend runtime health endpoint
- frontend runtime dashboard
- Ollama reachability panel
- storage path status panel
- safe config visibility
- runtime smoke test

This improves operator visibility before deployment work.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack T Completed",
    r'''
## Release Pack T Completed

Name:

Runtime Health UI + Dev Operator Dashboard

Added files:

- backend/src/api/runtime.py
- backend/tests/smoke_test_runtime.py
- frontend/src/app/runtime/page.tsx
- docs/runtime-health.md

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- README.md
- docs/production-readiness.md
- docs/project-status.md

Added behavior:

- GET /runtime/health
- read-only runtime frontend page
- Ollama reachability diagnostics
- storage path diagnostics
- safe public config summary
- runtime smoke test

Next recommended Release Pack:

Release Pack U: AI Generation Operator UI

Suggested scope:

- safe single-content generation page
- model list selector
- project selector
- content type selector
- save_output toggle
- generated asset link
- no batch execution from UI yet
    ''',
)


patch_main()
patch_api_init()
patch_frontend_nav()
patch_frontend_check()
patch_backend_check()

print("Release Pack T applied successfully.")
