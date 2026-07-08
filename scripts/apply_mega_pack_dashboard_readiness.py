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
    "backend/src/services/dashboard_service.py",
    """
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database
from src.services.system_service import SystemService


class DashboardServiceError(RuntimeError):
    pass


class DashboardService:
    @classmethod
    def get_summary(cls) -> dict[str, Any]:
        initialize_database()

        return {
            "system": SystemService.get_status(),
            "projects": cls._get_project_summary(),
            "content_assets": cls._get_content_asset_summary(),
            "exports": cls._get_export_summary(),
            "readiness": cls._get_readiness_summary(),
        }

    @classmethod
    def _get_project_summary(cls) -> dict[str, Any]:
        with get_connection() as connection:
            total_projects = connection.execute(
                "SELECT COUNT(*) AS count FROM projects"
            ).fetchone()["count"]

            projects_by_status_rows = connection.execute(
                '''
                SELECT status, COUNT(*) AS count
                FROM projects
                GROUP BY status
                ORDER BY status ASC
                '''
            ).fetchall()

            projects_by_type_rows = connection.execute(
                '''
                SELECT project_type, COUNT(*) AS count
                FROM projects
                GROUP BY project_type
                ORDER BY project_type ASC
                '''
            ).fetchall()

            recent_project_rows = connection.execute(
                '''
                SELECT
                    id,
                    name,
                    slug,
                    project_type,
                    language,
                    description,
                    status,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY created_at DESC
                LIMIT 5
                '''
            ).fetchall()

        return {
            "total": total_projects,
            "by_status": {
                row["status"]: row["count"]
                for row in projects_by_status_rows
            },
            "by_type": {
                row["project_type"]: row["count"]
                for row in projects_by_type_rows
            },
            "recent": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "project_type": row["project_type"],
                    "language": row["language"],
                    "description": row["description"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in recent_project_rows
            ],
        }

    @classmethod
    def _get_content_asset_summary(cls) -> dict[str, Any]:
        with get_connection() as connection:
            total_assets = connection.execute(
                "SELECT COUNT(*) AS count FROM content_assets"
            ).fetchone()["count"]

            assets_by_status_rows = connection.execute(
                '''
                SELECT status, COUNT(*) AS count
                FROM content_assets
                GROUP BY status
                ORDER BY status ASC
                '''
            ).fetchall()

            assets_by_type_rows = connection.execute(
                '''
                SELECT content_type, COUNT(*) AS count
                FROM content_assets
                GROUP BY content_type
                ORDER BY content_type ASC
                '''
            ).fetchall()

            assets_by_source_rows = connection.execute(
                '''
                SELECT source, COUNT(*) AS count
                FROM content_assets
                GROUP BY source
                ORDER BY source ASC
                '''
            ).fetchall()

            recent_asset_rows = connection.execute(
                '''
                SELECT
                    id,
                    project_id,
                    content_type,
                    title,
                    status,
                    source,
                    created_at,
                    updated_at
                FROM content_assets
                ORDER BY created_at DESC
                LIMIT 5
                '''
            ).fetchall()

        return {
            "total": total_assets,
            "by_status": {
                row["status"]: row["count"]
                for row in assets_by_status_rows
            },
            "by_content_type": {
                row["content_type"]: row["count"]
                for row in assets_by_type_rows
            },
            "by_source": {
                row["source"]: row["count"]
                for row in assets_by_source_rows
            },
            "recent": [
                {
                    "id": row["id"],
                    "project_id": row["project_id"],
                    "content_type": row["content_type"],
                    "title": row["title"],
                    "status": row["status"],
                    "source": row["source"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in recent_asset_rows
            ],
        }

    @staticmethod
    def _get_export_summary() -> dict[str, Any]:
        backend_root = Path(__file__).resolve().parents[2]
        export_root = backend_root / "exports"

        markdown_files = list(export_root.rglob("*.md")) if export_root.exists() else []

        recent_files = sorted(
            markdown_files,
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:5]

        return {
            "total_markdown_files": len(markdown_files),
            "export_root": str(export_root),
            "recent": [
                {
                    "file_name": item.name,
                    "file_path": str(item),
                    "size_bytes": item.stat().st_size,
                }
                for item in recent_files
            ],
        }

    @classmethod
    def _get_readiness_summary(cls) -> dict[str, Any]:
        project_summary = cls._get_project_summary()
        content_asset_summary = cls._get_content_asset_summary()
        export_summary = cls._get_export_summary()

        has_projects = project_summary["total"] > 0
        has_content_assets = content_asset_summary["total"] > 0
        has_exports = export_summary["total_markdown_files"] > 0

        return {
            "has_projects": has_projects,
            "has_content_assets": has_content_assets,
            "has_exports": has_exports,
            "dashboard_ready": True,
            "workflow_ready": has_projects and has_content_assets,
            "export_ready": has_content_assets,
        }
    """,
)


write_file(
    "backend/src/api/dashboard.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary() -> dict[str, Any]:
    return DashboardService.get_summary()
    """,
)


append_once(
    "backend/src/api/__init__.py",
    "dashboard_router",
    "from .dashboard import router as dashboard_router",
)

append_once(
    "backend/src/main.py",
    "dashboard_router",
    '''
from src.api.dashboard import router as dashboard_router

app.include_router(dashboard_router)
    ''',
)


write_file(
    "backend/tests/smoke_test_dashboard.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA dashboard smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Dashboard Project {uuid4().hex[:8]}"

    print("Creating dashboard test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Dashboard smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating dashboard test content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Dashboard Test Asset",
            "body": "Dashboard test asset body.",
            "status": "draft",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    print("Content asset created.")

    print("Checking GET /dashboard/summary...")
    summary_response = client.get("/dashboard/summary")
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()

    assert "system" in summary
    assert "projects" in summary
    assert "content_assets" in summary
    assert "exports" in summary
    assert "readiness" in summary

    assert summary["projects"]["total"] >= 1
    assert summary["content_assets"]["total"] >= 1
    assert summary["readiness"]["dashboard_ready"] is True
    assert summary["readiness"]["workflow_ready"] is True
    assert isinstance(summary["projects"]["recent"], list)
    assert isinstance(summary["content_assets"]["recent"], list)

    print("GET /dashboard/summary OK.")
    print("DAMA dashboard smoke test passed.")


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

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

if (-not (Test-Path $AISmokeTestPath)) {
    throw "AI smoke test was not found at $AISmokeTestPath"
}

if (-not (Test-Path $ProjectSmokeTestPath)) {
    throw "Project smoke test was not found at $ProjectSmokeTestPath"
}

if (-not (Test-Path $ContentAssetSmokeTestPath)) {
    throw "Content asset smoke test was not found at $ContentAssetSmokeTestPath"
}

if (-not (Test-Path $GenerationStorageSmokeTestPath)) {
    throw "Generation storage smoke test was not found at $GenerationStorageSmokeTestPath"
}

if (-not (Test-Path $ProjectWorkflowSmokeTestPath)) {
    throw "Project workflow smoke test was not found at $ProjectWorkflowSmokeTestPath"
}

if (-not (Test-Path $WorkflowAutomationSmokeTestPath)) {
    throw "Workflow automation smoke test was not found at $WorkflowAutomationSmokeTestPath"
}

if (-not (Test-Path $ExportSmokeTestPath)) {
    throw "Export smoke test was not found at $ExportSmokeTestPath"
}

if (-not (Test-Path $BatchGenerationSmokeTestPath)) {
    throw "Batch generation smoke test was not found at $BatchGenerationSmokeTestPath"
}

if (-not (Test-Path $DashboardSmokeTestPath)) {
    throw "Dashboard smoke test was not found at $DashboardSmokeTestPath"
}

Write-Host "Running DAMA backend AI smoke test..."
& $PythonPath $AISmokeTestPath

Write-Host ""
Write-Host "Running DAMA project persistence smoke test..."
& $PythonPath $ProjectSmokeTestPath

Write-Host ""
Write-Host "Running DAMA content asset smoke test..."
& $PythonPath $ContentAssetSmokeTestPath

Write-Host ""
Write-Host "Running DAMA generation storage smoke test..."
& $PythonPath $GenerationStorageSmokeTestPath

Write-Host ""
Write-Host "Running DAMA project workflow smoke test..."
& $PythonPath $ProjectWorkflowSmokeTestPath

Write-Host ""
Write-Host "Running DAMA workflow automation smoke test..."
& $PythonPath $WorkflowAutomationSmokeTestPath

Write-Host ""
Write-Host "Running DAMA export smoke test..."
& $PythonPath $ExportSmokeTestPath

Write-Host ""
Write-Host "Running DAMA batch generation smoke test..."
& $PythonPath $BatchGenerationSmokeTestPath

Write-Host ""
Write-Host "Running DAMA dashboard smoke test..."
& $PythonPath $DashboardSmokeTestPath

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
    "docs/backend-api.md",
    "## Dashboard API",
    """
## Dashboard API

The dashboard API provides an aggregated backend summary for future UI development.

GET /dashboard/summary

Returns:

- system status
- project totals
- project counts by status
- project counts by type
- recent projects
- content asset totals
- content asset counts by status
- content asset counts by content type
- content asset counts by source
- recent content assets
- export file summary
- readiness flags

Current readiness flags:

dashboard_ready

True when the dashboard API is available.

workflow_ready

True when the system has at least one project and one content asset.

export_ready

True when the system has at least one content asset.
    """,
)


append_once(
    "docs/project-status.md",
    "## Mega Pack E Completed",
    """
## Mega Pack E Completed

Name:

Dashboard Readiness API

Added files:

- backend/src/services/dashboard_service.py
- backend/src/api/dashboard.py
- backend/tests/smoke_test_dashboard.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoint:

GET /dashboard/summary

Purpose:

Prepare DAMA for future frontend/dashboard development by exposing one aggregated operational summary endpoint.

Next recommended Mega Pack:

Mega Pack F: API Quality and Error Standardization

Suggested scope:

- standard API error payload
- request validation consistency
- response envelope decision
- lightweight API quality docs
- smoke tests for common error shapes
    """,
)

print("Mega Pack E applied successfully.")
