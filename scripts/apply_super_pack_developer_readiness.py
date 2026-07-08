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
    "backend/src/services/developer_service.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute


class DeveloperServiceError(RuntimeError):
    pass


class DeveloperService:
    @classmethod
    def get_endpoint_map(cls, app: FastAPI) -> dict[str, Any]:
        endpoints: list[dict[str, Any]] = []

        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            methods = sorted(method for method in route.methods if method not in {"HEAD", "OPTIONS"})

            endpoints.append(
                {
                    "path": route.path,
                    "name": route.name,
                    "methods": methods,
                    "tags": list(route.tags),
                    "summary": route.summary,
                    "response_model": cls._response_model_name(route),
                }
            )

        endpoints.sort(key=lambda item: (item["path"], ",".join(item["methods"])))

        return {
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
        }

    @classmethod
    def get_frontend_contract(cls, app: FastAPI) -> dict[str, Any]:
        endpoint_map = cls.get_endpoint_map(app)

        return {
            "name": "DAMA Frontend Contract",
            "version": "1.0.0",
            "backend_base_url": "http://127.0.0.1:8000",
            "interactive_docs": "http://127.0.0.1:8000/docs",
            "openapi_json": "http://127.0.0.1:8000/openapi.json",
            "recommended_frontend_sections": [
                {
                    "key": "dashboard",
                    "title": "Dashboard",
                    "primary_endpoints": [
                        "GET /dashboard/summary",
                        "GET /maintenance/status",
                        "GET /system/status",
                    ],
                },
                {
                    "key": "projects",
                    "title": "Projects",
                    "primary_endpoints": [
                        "GET /projects",
                        "POST /projects",
                        "GET /projects/{project_id}",
                        "GET /projects/{project_id}/summary",
                        "PATCH /projects/{project_id}/status",
                    ],
                },
                {
                    "key": "content_assets",
                    "title": "Content Assets",
                    "primary_endpoints": [
                        "GET /content-assets",
                        "POST /content-assets",
                        "GET /content-assets/{asset_id}",
                        "PATCH /content-assets/{asset_id}/status",
                    ],
                },
                {
                    "key": "workflows",
                    "title": "Workflows",
                    "primary_endpoints": [
                        "GET /workflows/projects/{project_id}/output-plan",
                        "POST /workflows/projects/{project_id}/draft-assets",
                        "POST /workflows/projects/{project_id}/generate",
                        "POST /workflows/projects/{project_id}/batch-generate",
                    ],
                },
                {
                    "key": "exports",
                    "title": "Exports",
                    "primary_endpoints": [
                        "POST /exports/content-assets/{asset_id}/markdown",
                        "POST /exports/projects/{project_id}/bundle",
                    ],
                },
                {
                    "key": "developer",
                    "title": "Developer",
                    "primary_endpoints": [
                        "GET /developer/endpoint-map",
                        "GET /developer/frontend-contract",
                        "GET /developer/runbook",
                    ],
                },
            ],
            "error_shape": {
                "error": {
                    "type": "http_error | validation_error",
                    "status_code": "number",
                    "message": "string",
                    "path": "string",
                    "details": "optional list for validation errors",
                }
            },
            "endpoint_count": endpoint_map["total_endpoints"],
        }

    @staticmethod
    def get_runbook() -> dict[str, Any]:
        return {
            "name": "DAMA Local Operator Runbook",
            "version": "1.0.0",
            "local_backend_command": "cd I:\\\\DAMA\\\\backend && .\\\\.venv\\\\Scripts\\\\python.exe -m uvicorn src.main:app --reload",
            "backend_check_command": "cd I:\\\\DAMA && powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\\\scripts\\\\backend-check.ps1",
            "swagger_url": "http://127.0.0.1:8000/docs",
            "core_checks": [
                "GET /api",
                "GET /dashboard/summary",
                "GET /maintenance/status",
                "GET /system/status",
                "GET /developer/endpoint-map",
            ],
            "safe_workflow_order": [
                "Create project",
                "Create or generate content assets",
                "Review project summary",
                "Export content asset or project bundle",
                "Run maintenance backup",
            ],
            "git_workflow": [
                "git status",
                "git add <changed files>",
                "git commit -m <message>",
                "git push",
            ],
        }

    @staticmethod
    def _response_model_name(route: APIRoute) -> str | None:
        response_model = route.response_model

        if response_model is None:
            return None

        return getattr(response_model, "__name__", str(response_model))
    """,
)


write_file(
    "backend/src/api/developer.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.services.developer_service import DeveloperService


router = APIRouter(prefix="/developer", tags=["developer"])


@router.get("/endpoint-map")
def endpoint_map(request: Request) -> dict[str, Any]:
    return DeveloperService.get_endpoint_map(request.app)


@router.get("/frontend-contract")
def frontend_contract(request: Request) -> dict[str, Any]:
    return DeveloperService.get_frontend_contract(request.app)


@router.get("/runbook")
def runbook() -> dict[str, Any]:
    return DeveloperService.get_runbook()
    """,
)


append_once(
    "backend/src/api/__init__.py",
    "developer_router",
    "from .developer import router as developer_router",
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
from src.api.developer import router as developer_router
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
app.include_router(developer_router)
    """,
)


write_file(
    "backend/tests/smoke_test_developer.py",
    """
from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA developer readiness smoke test started.")

    client = TestClient(app)

    print("Checking GET /developer/endpoint-map...")
    endpoint_map_response = client.get("/developer/endpoint-map")
    assert endpoint_map_response.status_code == 200, endpoint_map_response.text
    endpoint_map = endpoint_map_response.json()
    assert endpoint_map["total_endpoints"] > 0
    paths = {endpoint["path"] for endpoint in endpoint_map["endpoints"]}
    assert "/dashboard/summary" in paths
    assert "/developer/endpoint-map" in paths
    assert "/projects" in paths
    print("GET /developer/endpoint-map OK.")

    print("Checking GET /developer/frontend-contract...")
    contract_response = client.get("/developer/frontend-contract")
    assert contract_response.status_code == 200, contract_response.text
    contract = contract_response.json()
    assert contract["name"] == "DAMA Frontend Contract"
    assert contract["backend_base_url"] == "http://127.0.0.1:8000"
    assert contract["endpoint_count"] == endpoint_map["total_endpoints"]
    assert contract["recommended_frontend_sections"]
    print("GET /developer/frontend-contract OK.")

    print("Checking GET /developer/runbook...")
    runbook_response = client.get("/developer/runbook")
    assert runbook_response.status_code == 200, runbook_response.text
    runbook = runbook_response.json()
    assert runbook["name"] == "DAMA Local Operator Runbook"
    assert runbook["core_checks"]
    assert runbook["safe_workflow_order"]
    print("GET /developer/runbook OK.")

    print("DAMA developer readiness smoke test passed.")


if __name__ == "__main__":
    main()
    """,
)


write_file(
    "docs/operator-guide.md",
    """
# DAMA Operator Guide

This guide explains how to run, check, and maintain DAMA locally.

## Local Backend

Run the backend:

    cd I:\\DAMA\\backend
    .\\.venv\\Scripts\\python.exe -m uvicorn src.main:app --reload

Open Swagger:

    http://127.0.0.1:8000/docs

Open OpenAPI JSON:

    http://127.0.0.1:8000/openapi.json

## Backend Check

Run all backend smoke tests:

    cd I:\\DAMA
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\backend-check.ps1

## Core Operational Endpoints

    GET /api
    GET /dashboard/summary
    GET /maintenance/status
    GET /system/status
    GET /developer/endpoint-map
    GET /developer/frontend-contract
    GET /developer/runbook

## Safe Working Order

1. Create a project.
2. Create draft assets or generate project content.
3. Review project summary.
4. Export content asset or project bundle.
5. Run database backup.
6. Commit and push stable changes.

## Backup

Create local database backup:

    POST /maintenance/database/backup

Backup directory:

    backend/backups

The backup directory is ignored by Git.
    """,
)


write_file(
    "docs/frontend-contract.md",
    """
# DAMA Frontend Contract

This document defines the first backend contract for a future DAMA dashboard.

## Base URL

    http://127.0.0.1:8000

## Interactive API Docs

    http://127.0.0.1:8000/docs

## OpenAPI JSON

    http://127.0.0.1:8000/openapi.json

## Recommended Frontend Sections

## Dashboard

Primary endpoints:

    GET /dashboard/summary
    GET /maintenance/status
    GET /system/status

## Projects

Primary endpoints:

    GET /projects
    POST /projects
    GET /projects/{project_id}
    GET /projects/{project_id}/summary
    PATCH /projects/{project_id}/status

## Content Assets

Primary endpoints:

    GET /content-assets
    POST /content-assets
    GET /content-assets/{asset_id}
    PATCH /content-assets/{asset_id}/status

## Workflows

Primary endpoints:

    GET /workflows/projects/{project_id}/output-plan
    POST /workflows/projects/{project_id}/draft-assets
    POST /workflows/projects/{project_id}/generate
    POST /workflows/projects/{project_id}/batch-generate

## Exports

Primary endpoints:

    POST /exports/content-assets/{asset_id}/markdown
    POST /exports/projects/{project_id}/bundle

## Developer

Primary endpoints:

    GET /developer/endpoint-map
    GET /developer/frontend-contract
    GET /developer/runbook

## Standard Error Shape

HTTP errors:

    {
      "error": {
        "type": "http_error",
        "status_code": 404,
        "message": "Project not found.",
        "path": "/projects/missing-project-id"
      }
    }

Validation errors:

    {
      "error": {
        "type": "validation_error",
        "status_code": 422,
        "message": "Request validation failed.",
        "path": "/projects",
        "details": []
      }
    }
    """,
)


write_file(
    "docs/workflow-example.md",
    """
# DAMA Project Workflow Example

This document shows a typical DAMA workflow.

## 1. Create Project

Endpoint:

    POST /projects

Example body:

    {
      "name": "DAMA Launch Campaign",
      "project_type": "content_campaign",
      "description": "Launch campaign for DAMA."
    }

## 2. Get Output Plan

Endpoint:

    GET /workflows/projects/{project_id}/output-plan

Purpose:

Create a plan from project content types.

## 3. Create Draft Assets

Endpoint:

    POST /workflows/projects/{project_id}/draft-assets

Purpose:

Create draft content asset records for the project.

## 4. Generate and Save One Asset

Endpoint:

    POST /workflows/projects/{project_id}/generate

Purpose:

Generate one project-aware content asset and store it.

## 5. Batch Generation Dry Run

Endpoint:

    POST /workflows/projects/{project_id}/batch-generate

Use dry run first:

    {
      "model": "qwen2.5-coder:7b",
      "dry_run": true,
      "max_outputs": 2
    }

## 6. Project Summary

Endpoint:

    GET /projects/{project_id}/summary

Purpose:

Review counts by status and content type.

## 7. Export Project Bundle

Endpoint:

    POST /exports/projects/{project_id}/bundle

Purpose:

Create Markdown bundle from all project content assets.

## 8. Backup Database

Endpoint:

    POST /maintenance/database/backup

Purpose:

Create local backup before major changes.
    """,
)


write_file(
    "scripts/backend-check.ps1",
    """
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\\backend\\.venv\\Scripts\\python.exe"

$SmokeTests = @(
    ".\\backend\\tests\\smoke_test_ai.py",
    ".\\backend\\tests\\smoke_test_projects.py",
    ".\\backend\\tests\\smoke_test_content_assets.py",
    ".\\backend\\tests\\smoke_test_generation_storage.py",
    ".\\backend\\tests\\smoke_test_project_workflow.py",
    ".\\backend\\tests\\smoke_test_workflow_automation.py",
    ".\\backend\\tests\\smoke_test_exports.py",
    ".\\backend\\tests\\smoke_test_batch_generation.py",
    ".\\backend\\tests\\smoke_test_dashboard.py",
    ".\\backend\\tests\\smoke_test_maintenance.py",
    ".\\backend\\tests\\smoke_test_developer.py"
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
            "developer": {
                "description": "Developer endpoint map, frontend contract, and local runbook.",
                "endpoints": [
                    "GET /developer/endpoint-map",
                    "GET /developer/frontend-contract",
                    "GET /developer/runbook",
                ],
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
    "docs/backend-api.md",
    "## Developer API",
    """
## Developer API

The developer API helps future frontend and operator workflows.

GET /developer/endpoint-map

Returns all FastAPI routes with path, methods, tags, name, and response model.

GET /developer/frontend-contract

Returns the first frontend contract for the future DAMA dashboard.

GET /developer/runbook

Returns the local operator runbook as structured JSON.
    """,
)


append_once(
    "docs/project-status.md",
    "## Super Pack G Completed",
    """
## Super Pack G Completed

Name:

Developer Readiness + Frontend Contract + Operator Docs

Added files:

- backend/src/services/developer_service.py
- backend/src/api/developer.py
- backend/tests/smoke_test_developer.py
- docs/operator-guide.md
- docs/frontend-contract.md
- docs/workflow-example.md

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

GET /developer/endpoint-map

GET /developer/frontend-contract

GET /developer/runbook

Purpose:

Prepare DAMA for faster frontend development, easier local operation, and cleaner developer handoff.

Next recommended Super Pack:

Super Pack H: Frontend Foundation

Suggested scope:

- create frontend package baseline
- create simple dashboard structure
- define API client
- define page map
- no heavy UI framework decision beyond current project stack unless confirmed
    """,
)

print("Super Pack G applied successfully.")
