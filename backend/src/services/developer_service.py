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
            "local_backend_command": "cd I:\\DAMA\\backend && .\\.venv\\Scripts\\python.exe -m uvicorn src.main:app --reload",
            "backend_check_command": "cd I:\\DAMA && powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\backend-check.ps1",
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
