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
    "backend/src/api/index.py",
    '''
from __future__ import annotations

from typing import Any

from fastapi import APIRouter


router = APIRouter()


def _capability(
    *,
    key: str,
    description: str,
    endpoints: list[str],
) -> dict[str, Any]:
    return {
        "key": key,
        "description": description,
        "endpoints": endpoints,
    }


@router.get("/api")
def api_index() -> dict[str, Any]:
    capabilities = [
        _capability(
            key="dashboard",
            description="Aggregated dashboard readiness and operational summary.",
            endpoints=["GET /dashboard/summary"],
        ),
        _capability(
            key="developer",
            description="Developer endpoint map, frontend contract, and local runbook.",
            endpoints=[
                "GET /developer/endpoint-map",
                "GET /developer/frontend-contract",
                "GET /developer/runbook",
            ],
        ),
        _capability(
            key="maintenance",
            description="Maintenance status, database status, and local database backup.",
            endpoints=[
                "GET /maintenance/status",
                "POST /maintenance/database/backup",
            ],
        ),
        _capability(
            key="models",
            description="Local AI model discovery.",
            endpoints=["GET /models"],
        ),
        _capability(
            key="generation",
            description="Raw text generation through AI providers.",
            endpoints=["POST /generate"],
        ),
        _capability(
            key="content",
            description="Structured content generation, content type catalog, and optional output storage.",
            endpoints=[
                "GET /content/types",
                "GET /content/types/{key}",
                "POST /content/generate",
            ],
        ),
        _capability(
            key="content_assets",
            description="Persisted content assets connected to projects.",
            endpoints=[
                "POST /content-assets",
                "GET /content-assets",
                "GET /content-assets/{asset_id}",
                "PATCH /content-assets/{asset_id}/status",
            ],
        ),
        _capability(
            key="exports",
            description="Markdown exports for content assets and project bundles.",
            endpoints=[
                "POST /exports/content-assets/{asset_id}/markdown",
                "POST /exports/projects/{project_id}/bundle",
            ],
        ),
        _capability(
            key="providers",
            description="AI provider catalog.",
            endpoints=[
                "GET /providers",
                "GET /providers/{key}",
            ],
        ),
        _capability(
            key="projects",
            description="Project records, project workflow status, project content assets, and project summaries.",
            endpoints=[
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
        ),
        _capability(
            key="workflows",
            description="Project-aware content workflow automation and batch generation planning.",
            endpoints=[
                "GET /workflows/projects/{project_id}/output-plan",
                "POST /workflows/projects/{project_id}/draft-assets",
                "POST /workflows/projects/{project_id}/generate",
                "POST /workflows/projects/{project_id}/batch-generate",
            ],
        ),
        _capability(
            key="system",
            description="Runtime system status.",
            endpoints=["GET /system/status"],
        ),
    ]

    capabilities_by_key = {
        capability["key"]: {
            "description": capability["description"],
            "endpoints": capability["endpoints"],
        }
        for capability in capabilities
    }

    return {
        "name": "DAMA Backend API",
        "version": "1.0.0",
        "description": "Backend API for the DAMA AI Content Automation Platform.",
        "capabilities": capabilities,
        "capabilities_by_key": capabilities_by_key,
    }
    ''',
)


append_once(
    "docs/project-status.md",
    "## API Capability Compatibility Hotfix",
    '''
## API Capability Compatibility Hotfix

The API index endpoint now returns capabilities in two formats:

- capabilities: list format for backward compatibility with smoke tests
- capabilities_by_key: dictionary format for frontend and developer usage

Purpose:

Keep old checks stable while preserving key-based API discovery.
    ''',
)

print("API capability compatibility hotfix applied.")
