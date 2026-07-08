from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


write_file(
    "backend/src/services/developer_service.py",
    r'''
from __future__ import annotations

from typing import Any

from fastapi import FastAPI


class DeveloperServiceError(RuntimeError):
    pass


class DeveloperService:
    @classmethod
    def get_endpoint_map(cls, app: FastAPI) -> dict[str, Any]:
        openapi_schema = app.openapi()
        paths = openapi_schema.get("paths", {})

        endpoints: list[dict[str, Any]] = []

        for path, method_map in paths.items():
            methods: list[str] = []
            tags: set[str] = set()
            summaries: list[str] = []
            operation_ids: list[str] = []

            for method, operation in method_map.items():
                if method.lower() not in {
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "options",
                    "head",
                }:
                    continue

                methods.append(method.upper())

                for tag in operation.get("tags", []):
                    tags.add(str(tag))

                if operation.get("summary"):
                    summaries.append(str(operation["summary"]))

                if operation.get("operationId"):
                    operation_ids.append(str(operation["operationId"]))

            endpoints.append(
                {
                    "path": path,
                    "name": operation_ids[0] if operation_ids else path,
                    "methods": sorted(methods),
                    "tags": sorted(tags),
                    "summary": summaries[0] if summaries else None,
                    "response_model": None,
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
    ''',
)

print("Developer endpoint map hotfix applied.")
