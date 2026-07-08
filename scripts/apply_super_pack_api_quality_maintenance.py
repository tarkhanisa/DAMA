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
    "backend/src/services/maintenance_service.py",
    """
from __future__ import annotations

import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.database.sqlite_database import get_database_path, initialize_database


class MaintenanceServiceError(RuntimeError):
    pass


class MaintenanceService:
    @classmethod
    def get_status(cls) -> dict[str, Any]:
        initialize_database()

        database_path = get_database_path()
        backend_root = Path(__file__).resolve().parents[2]
        export_root = backend_root / "exports"
        backup_root = backend_root / "backups"

        return {
            "database": cls._get_database_status(database_path),
            "exports": cls._get_directory_status(export_root, pattern="*.md"),
            "backups": cls._get_directory_status(backup_root, pattern="*.db"),
            "maintenance_ready": True,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def backup_database(cls) -> dict[str, Any]:
        initialize_database()

        database_path = get_database_path()

        if not database_path.exists():
            raise MaintenanceServiceError("Database file does not exist.")

        backend_root = Path(__file__).resolve().parents[2]
        backup_root = backend_root / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_file = backup_root / f"dama-{timestamp}.db"

        shutil.copy2(database_path, backup_file)

        return {
            "backup_created": True,
            "source_path": str(database_path),
            "backup_path": str(backup_file),
            "size_bytes": backup_file.stat().st_size,
            "created_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def _get_database_status(cls, database_path: Path) -> dict[str, Any]:
        database_exists = database_path.exists()

        status: dict[str, Any] = {
            "path": str(database_path),
            "exists": database_exists,
            "size_bytes": database_path.stat().st_size if database_exists else 0,
            "tables": {},
        }

        if not database_exists:
            return status

        try:
            with sqlite3.connect(database_path) as connection:
                connection.row_factory = sqlite3.Row

                table_rows = connection.execute(
                    '''
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    ORDER BY name ASC
                    '''
                ).fetchall()

                for row in table_rows:
                    table_name = row["name"]

                    if table_name.startswith("sqlite_"):
                        continue

                    count_row = connection.execute(
                        f"SELECT COUNT(*) AS count FROM {table_name}"
                    ).fetchone()

                    status["tables"][table_name] = count_row["count"]
        except sqlite3.Error as exc:
            status["error"] = str(exc)

        return status

    @staticmethod
    def _get_directory_status(directory: Path, *, pattern: str) -> dict[str, Any]:
        files = list(directory.rglob(pattern)) if directory.exists() else []

        total_size = sum(file_path.stat().st_size for file_path in files)

        recent_files = sorted(
            files,
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:5]

        return {
            "path": str(directory),
            "exists": directory.exists(),
            "file_count": len(files),
            "total_size_bytes": total_size,
            "recent": [
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                }
                for file_path in recent_files
            ],
        }
    """,
)


write_file(
    "backend/src/api/maintenance.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.maintenance_service import (
    MaintenanceService,
    MaintenanceServiceError,
)


router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/status")
def maintenance_status() -> dict[str, Any]:
    return MaintenanceService.get_status()


@router.post("/database/backup")
def backup_database() -> dict[str, Any]:
    try:
        return MaintenanceService.backup_database()
    except MaintenanceServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    """,
)


append_once(
    "backend/src/api/__init__.py",
    "maintenance_router",
    "from .maintenance import router as maintenance_router",
)


write_file(
    "backend/src/main.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.content import router as content_router
from src.api.content_assets import router as content_assets_router
from src.api.content_generation import router as content_generation_router
from src.api.dashboard import router as dashboard_router
from src.api.exports import router as exports_router
from src.api.generate import router as generate_router
from src.api.health import router as health_router
from src.api.index import router as index_router
from src.api.maintenance import router as maintenance_router
from src.api.models import router as models_router
from src.api.projects import router as projects_router
from src.api.providers import router as providers_router
from src.api.system import router as system_router
from src.api.workflows import router as workflows_router


app = FastAPI(
    title="DAMA Backend",
    description="AI Content Automation Platform backend.",
    version="1.0.0",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "status_code": exc.status_code,
                "message": str(exc.detail),
                "path": request.url.path,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "status_code": 422,
                "message": "Request validation failed.",
                "path": request.url.path,
                "details": exc.errors(),
            }
        },
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "DAMA",
        "status": "running",
        "api": "/api",
        "docs": "/docs",
    }


app.include_router(index_router)
app.include_router(health_router)
app.include_router(content_router)
app.include_router(models_router)
app.include_router(generate_router)
app.include_router(content_generation_router)
app.include_router(providers_router)
app.include_router(system_router)
app.include_router(projects_router)
app.include_router(content_assets_router)
app.include_router(workflows_router)
app.include_router(exports_router)
app.include_router(dashboard_router)
app.include_router(maintenance_router)
    """,
)


write_file(
    "backend/tests/smoke_test_maintenance.py",
    """
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA maintenance smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Maintenance Project {uuid4().hex[:8]}"

    print("Creating maintenance test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Maintenance smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating maintenance test content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Maintenance Test Asset",
            "body": "Maintenance test asset body.",
            "status": "draft",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    print("Content asset created.")

    print("Checking GET /maintenance/status...")
    status_response = client.get("/maintenance/status")
    assert status_response.status_code == 200, status_response.text
    status = status_response.json()

    assert status["maintenance_ready"] is True
    assert status["database"]["exists"] is True
    assert status["database"]["tables"]["projects"] >= 1
    assert status["database"]["tables"]["content_assets"] >= 1
    assert "exports" in status
    assert "backups" in status
    print("GET /maintenance/status OK.")

    print("Checking POST /maintenance/database/backup...")
    backup_response = client.post("/maintenance/database/backup")
    assert backup_response.status_code == 200, backup_response.text
    backup = backup_response.json()

    assert backup["backup_created"] is True
    assert Path(backup["backup_path"]).exists()
    assert backup["size_bytes"] > 0
    print("POST /maintenance/database/backup OK.")

    print("Checking standardized 404 error shape...")
    missing_response = client.get("/projects/missing-project-id")
    assert missing_response.status_code == 404
    missing_error = missing_response.json()["error"]
    assert missing_error["type"] == "http_error"
    assert missing_error["status_code"] == 404
    assert missing_error["path"] == "/projects/missing-project-id"
    print("Standardized 404 error shape OK.")

    print("Checking standardized validation error shape...")
    validation_response = client.post(
        "/projects",
        json={
            "project_type": "content_campaign",
        },
    )
    assert validation_response.status_code == 422
    validation_error = validation_response.json()["error"]
    assert validation_error["type"] == "validation_error"
    assert validation_error["status_code"] == 422
    assert validation_error["path"] == "/projects"
    assert validation_error["details"]
    print("Standardized validation error shape OK.")

    print("DAMA maintenance smoke test passed.")


if __name__ == "__main__":
    main()
    """,
)


write_file(
    "scripts/backend-check.ps1",
    """
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\\backend\\.venv\\Scripts\\python.exe"
$AISmokeTestPath = ".\\backend\\tests\\smoke_test_ai.py"
$ProjectSmokeTestPath = ".\\backend\\tests\\smoke_test_projects.py"
$ContentAssetSmokeTestPath = ".\\backend\\tests\\smoke_test_content_assets.py"
$GenerationStorageSmokeTestPath = ".\\backend\\tests\\smoke_test_generation_storage.py"
$ProjectWorkflowSmokeTestPath = ".\\backend\\tests\\smoke_test_project_workflow.py"
$WorkflowAutomationSmokeTestPath = ".\\backend\\tests\\smoke_test_workflow_automation.py"
$ExportSmokeTestPath = ".\\backend\\tests\\smoke_test_exports.py"
$BatchGenerationSmokeTestPath = ".\\backend\\tests\\smoke_test_batch_generation.py"
$DashboardSmokeTestPath = ".\\backend\\tests\\smoke_test_dashboard.py"
$MaintenanceSmokeTestPath = ".\\backend\\tests\\smoke_test_maintenance.py"

$SmokeTests = @(
    $AISmokeTestPath,
    $ProjectSmokeTestPath,
    $ContentAssetSmokeTestPath,
    $GenerationStorageSmokeTestPath,
    $ProjectWorkflowSmokeTestPath,
    $WorkflowAutomationSmokeTestPath,
    $ExportSmokeTestPath,
    $BatchGenerationSmokeTestPath,
    $DashboardSmokeTestPath,
    $MaintenanceSmokeTestPath
)

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

foreach ($SmokeTest in $SmokeTests) {
    if (-not (Test-Path $SmokeTest)) {
        throw "Smoke test was not found at $SmokeTest"
    }
}

Write-Host "Running DAMA backend smoke tests..."

foreach ($SmokeTest in $SmokeTests) {
    Write-Host ""
    Write-Host "Running $SmokeTest..."
    & $PythonPath $SmokeTest
}

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
    """,
)


write_file(
    "backend/src/api/index.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter


router = APIRouter()


@router.get("/api")
def api_index() -> dict[str, Any]:
    return {
        "name": "DAMA Backend API",
        "version": "1.0.0",
        "description": "Backend API for the DAMA AI Content Automation Platform.",
        "capabilities": {
            "dashboard": {
                "description": "Aggregated dashboard readiness and operational summary.",
                "endpoints": ["GET /dashboard/summary"],
            },
            "maintenance": {
                "description": "Maintenance status, database status, and local database backup.",
                "endpoints": [
                    "GET /maintenance/status",
                    "POST /maintenance/database/backup",
                ],
            },
            "models": {
                "description": "Local AI model discovery.",
                "endpoints": ["GET /models"],
            },
            "generation": {
                "description": "Raw text generation through AI providers.",
                "endpoints": ["POST /generate"],
            },
            "content": {
                "description": "Structured content generation, content type catalog, and optional output storage.",
                "endpoints": [
                    "GET /content/types",
                    "GET /content/types/{key}",
                    "POST /content/generate",
                ],
            },
            "content_assets": {
                "description": "Persisted content assets connected to projects.",
                "endpoints": [
                    "POST /content-assets",
                    "GET /content-assets",
                    "GET /content-assets/{asset_id}",
                    "PATCH /content-assets/{asset_id}/status",
                ],
            },
            "exports": {
                "description": "Markdown exports for content assets and project bundles.",
                "endpoints": [
                    "POST /exports/content-assets/{asset_id}/markdown",
                    "POST /exports/projects/{project_id}/bundle",
                ],
            },
            "providers": {
                "description": "AI provider catalog.",
                "endpoints": ["GET /providers", "GET /providers/{key}"],
            },
            "projects": {
                "description": "Project records, project workflow status, project content assets, and project summaries.",
                "endpoints": [
                    "GET /projects/types",
                    "GET /projects/types/{key}",
                    "POST /projects/metadata",
                    "POST /projects",
                    "GET /projects",
                    "GET /projects/{project_id}",
                    "GET /projects/{project_id}/content-assets",
                    "GET /projects/{project_id}/summary",
                    "PATCH /projects/{project_id}/status",
                ],
            },
            "workflows": {
                "description": "Project-aware content workflow automation and batch generation planning.",
                "endpoints": [
                    "GET /workflows/projects/{project_id}/output-plan",
                    "POST /workflows/projects/{project_id}/draft-assets",
                    "POST /workflows/projects/{project_id}/generate",
                    "POST /workflows/projects/{project_id}/batch-generate",
                ],
            },
            "system": {
                "description": "Runtime system status.",
                "endpoints": ["GET /system/status"],
            },
        },
    }
    """,
)


append_once(
    ".gitignore",
    "backend/backups/",
    """
backend/backups/
    """,
)


append_once(
    "docs/backend-api.md",
    "## Maintenance API",
    """
## Maintenance API

The maintenance API provides local operational checks and database backup utilities.

GET /maintenance/status

Returns:

- database path
- database existence
- database size
- table row counts
- export directory status
- backup directory status
- maintenance readiness flag

POST /maintenance/database/backup

Creates a timestamped local SQLite database backup.

Current backup directory:

backend/backups

The backup directory is ignored by Git.

## Standard Error Shape

HTTP errors now use a standard shape:

error.type

Error category.

error.status_code

HTTP status code.

error.message

Human-readable message.

error.path

Request path.

Validation errors use:

error.type = validation_error

error.details

Validation detail list.
    """,
)


append_once(
    "docs/project-status.md",
    "## Super Pack F Completed",
    """
## Super Pack F Completed

Name:

API Quality + Maintenance + Developer Readiness

Added files:

- backend/src/services/maintenance_service.py
- backend/src/api/maintenance.py
- backend/tests/smoke_test_maintenance.py

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md
- .gitignore

Added endpoints:

GET /maintenance/status

POST /maintenance/database/backup

Added behavior:

- standardized HTTP error payload
- standardized validation error payload
- database status reporting
- export directory status reporting
- backup directory status reporting
- local SQLite backup creation
- cleaner backend-check smoke test runner

Purpose:

Make DAMA more maintainable, dashboard-ready, and safer to continue developing at higher speed.

Next recommended Super Pack:

Super Pack G: API Documentation + OpenAPI Readiness + Local Operator Guide

Suggested scope:

- generated endpoint map
- local operator guide
- backend runbook
- system lifecycle docs
- project workflow example docs
- frontend readiness contract
    """,
)

print("Super Pack F applied successfully.")
