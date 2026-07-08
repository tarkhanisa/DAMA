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
