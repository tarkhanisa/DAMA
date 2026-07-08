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
    "backend/src/services/export_service.py",
    """
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ExportServiceError(RuntimeError):
    pass


class InvalidExportRequestError(ExportServiceError):
    pass


@dataclass(frozen=True, slots=True)
class ExportResult:
    export_type: str
    file_name: str
    file_path: str
    title: str
    created_at: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "export_type": self.export_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "title": self.title,
            "created_at": self.created_at,
            "content": self.content,
        }


class ExportService:
    @classmethod
    def export_content_asset_markdown(
        cls,
        *,
        content_asset: dict[str, Any],
        export_root: Path | None = None,
    ) -> dict[str, Any]:
        asset_id = cls._required(content_asset.get("id"), "Content asset ID")
        title = cls._required(content_asset.get("title"), "Content asset title")
        body = cls._required(content_asset.get("body"), "Content asset body")
        content_type = cls._required(content_asset.get("content_type"), "Content type")
        status = cls._required(content_asset.get("status"), "Content asset status")
        source = cls._required(content_asset.get("source"), "Content asset source")
        project_id = cls._required(content_asset.get("project_id"), "Project ID")

        created_at = datetime.now(UTC).isoformat()

        markdown = cls._build_content_asset_markdown(
            title=title,
            body=body,
            content_type=content_type,
            status=status,
            source=source,
            project_id=project_id,
            asset_id=asset_id,
            created_at=created_at,
        )

        export_directory = cls._get_export_root(export_root) / "content-assets"
        export_directory.mkdir(parents=True, exist_ok=True)

        file_name = f"{cls._slugify(title)}-{asset_id[:8]}.md"
        file_path = export_directory / file_name

        file_path.write_text(markdown, encoding="utf-8")

        return ExportResult(
            export_type="content_asset_markdown",
            file_name=file_name,
            file_path=str(file_path),
            title=title,
            created_at=created_at,
            content=markdown,
        ).to_dict()

    @classmethod
    def export_project_markdown_bundle(
        cls,
        *,
        project: dict[str, Any],
        content_assets: list[dict[str, Any]],
        export_root: Path | None = None,
    ) -> dict[str, Any]:
        project_id = cls._required(project.get("id"), "Project ID")
        project_name = cls._required(project.get("name"), "Project name")
        project_type = cls._required(project.get("project_type"), "Project type")
        project_status = cls._required(project.get("status"), "Project status")

        created_at = datetime.now(UTC).isoformat()

        markdown = cls._build_project_bundle_markdown(
            project=project,
            content_assets=content_assets,
            created_at=created_at,
        )

        export_directory = cls._get_export_root(export_root) / "projects"
        export_directory.mkdir(parents=True, exist_ok=True)

        file_name = f"{cls._slugify(project_name)}-{project_id[:8]}-bundle.md"
        file_path = export_directory / file_name

        file_path.write_text(markdown, encoding="utf-8")

        return ExportResult(
            export_type="project_markdown_bundle",
            file_name=file_name,
            file_path=str(file_path),
            title=f"{project_name} Bundle",
            created_at=created_at,
            content=markdown,
        ).to_dict()

    @staticmethod
    def _build_content_asset_markdown(
        *,
        title: str,
        body: str,
        content_type: str,
        status: str,
        source: str,
        project_id: str,
        asset_id: str,
        created_at: str,
    ) -> str:
        return (
            f"# {title}\\n\\n"
            f"Asset ID: {asset_id}\\n\\n"
            f"Project ID: {project_id}\\n\\n"
            f"Content Type: {content_type}\\n\\n"
            f"Status: {status}\\n\\n"
            f"Source: {source}\\n\\n"
            f"Exported At: {created_at}\\n\\n"
            "---\\n\\n"
            f"{body}\\n"
        )

    @classmethod
    def _build_project_bundle_markdown(
        cls,
        *,
        project: dict[str, Any],
        content_assets: list[dict[str, Any]],
        created_at: str,
    ) -> str:
        project_name = cls._required(project.get("name"), "Project name")
        project_id = cls._required(project.get("id"), "Project ID")
        project_type = cls._required(project.get("project_type"), "Project type")
        project_status = cls._required(project.get("status"), "Project status")

        sections = [
            f"# {project_name}",
            "",
            f"Project ID: {project_id}",
            "",
            f"Project Type: {project_type}",
            "",
            f"Project Status: {project_status}",
            "",
            f"Exported At: {created_at}",
            "",
            f"Total Content Assets: {len(content_assets)}",
            "",
            "---",
            "",
        ]

        if not content_assets:
            sections.append("No content assets found for this project.")
            sections.append("")
            return "\\n".join(sections)

        for index, asset in enumerate(content_assets, start=1):
            title = cls._required(asset.get("title"), "Content asset title")
            body = cls._required(asset.get("body"), "Content asset body")
            content_type = cls._required(asset.get("content_type"), "Content type")
            status = cls._required(asset.get("status"), "Content asset status")
            source = cls._required(asset.get("source"), "Content asset source")
            asset_id = cls._required(asset.get("id"), "Content asset ID")

            sections.extend(
                [
                    f"## {index}. {title}",
                    "",
                    f"Asset ID: {asset_id}",
                    "",
                    f"Content Type: {content_type}",
                    "",
                    f"Status: {status}",
                    "",
                    f"Source: {source}",
                    "",
                    body,
                    "",
                    "---",
                    "",
                ]
            )

        return "\\n".join(sections)

    @staticmethod
    def _get_export_root(export_root: Path | None = None) -> Path:
        if export_root is not None:
            return export_root

        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / "exports"

    @staticmethod
    def _required(value: Any, field_name: str) -> str:
        normalized_value = str(value or "").strip()

        if not normalized_value:
            raise InvalidExportRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @staticmethod
    def _slugify(value: str) -> str:
        normalized_value = value.strip().lower()
        normalized_value = re.sub(r"[^a-z0-9]+", "-", normalized_value)
        normalized_value = normalized_value.strip("-")

        if not normalized_value:
            return "export"

        return normalized_value
    """,
)


write_file(
    "backend/src/api/exports.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.repositories.content_asset_repository import ContentAssetRepository
from src.repositories.project_repository import ProjectRepository
from src.services.export_service import ExportService, InvalidExportRequestError


router = APIRouter(prefix="/exports", tags=["exports"])


class ExportResponse(BaseModel):
    export_type: str
    file_name: str
    file_path: str
    title: str
    created_at: str
    content: str


@router.post("/content-assets/{asset_id}/markdown", response_model=ExportResponse)
def export_content_asset_markdown(asset_id: str) -> dict[str, Any]:
    repository = ContentAssetRepository()
    content_asset = repository.get_content_asset(asset_id)

    if content_asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    try:
        return ExportService.export_content_asset_markdown(
            content_asset=content_asset,
        )
    except InvalidExportRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/projects/{project_id}/bundle", response_model=ExportResponse)
def export_project_markdown_bundle(project_id: str) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content_asset_repository = ContentAssetRepository()
    content_assets = content_asset_repository.list_content_assets(project_id=project_id)

    try:
        return ExportService.export_project_markdown_bundle(
            project=project,
            content_assets=content_assets,
        )
    except InvalidExportRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    """,
)


append_once(
    "backend/src/api/__init__.py",
    "exports_router",
    "from .exports import router as exports_router",
)

append_once(
    "backend/src/main.py",
    "exports_router",
    """
from src.api.exports import router as exports_router

app.include_router(exports_router)
    """,
)


write_file(
    "backend/tests/smoke_test_exports.py",
    """
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA export smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Export Project {uuid4().hex[:8]}"

    print("Creating export test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Export smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating export test content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Export Test Asset",
            "body": "This is the body of the export test asset.",
            "status": "approved",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    asset = asset_response.json()
    asset_id = asset["id"]
    print("Content asset created.")

    print("Checking POST /exports/content-assets/{asset_id}/markdown...")
    asset_export_response = client.post(f"/exports/content-assets/{asset_id}/markdown")
    assert asset_export_response.status_code == 200, asset_export_response.text
    asset_export = asset_export_response.json()
    assert asset_export["export_type"] == "content_asset_markdown"
    assert "Export Test Asset" in asset_export["content"]
    assert "This is the body of the export test asset." in asset_export["content"]
    assert Path(asset_export["file_path"]).exists()
    print("Content asset export OK.")

    print("Checking POST /exports/projects/{project_id}/bundle...")
    project_export_response = client.post(f"/exports/projects/{project_id}/bundle")
    assert project_export_response.status_code == 200, project_export_response.text
    project_export = project_export_response.json()
    assert project_export["export_type"] == "project_markdown_bundle"
    assert project_name in project_export["content"]
    assert "Export Test Asset" in project_export["content"]
    assert Path(project_export["file_path"]).exists()
    print("Project bundle export OK.")

    print("Checking missing content asset export...")
    missing_asset_response = client.post("/exports/content-assets/missing-asset/markdown")
    assert missing_asset_response.status_code == 404
    print("Missing content asset export check OK.")

    print("Checking missing project export...")
    missing_project_response = client.post("/exports/projects/missing-project/bundle")
    assert missing_project_response.status_code == 404
    print("Missing project export check OK.")

    print("DAMA export smoke test passed.")


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
                "description": "Project-aware content workflow automation.",
                "endpoints": [
                    "GET /workflows/projects/{project_id}/output-plan",
                    "POST /workflows/projects/{project_id}/draft-assets",
                    "POST /workflows/projects/{project_id}/generate",
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
    "backend/exports/",
    """
backend/exports/
    """,
)


append_once(
    "docs/backend-api.md",
    "## Export API",
    """
## Export API

The export API creates Markdown files from stored DAMA content.

POST /exports/content-assets/{asset_id}/markdown

Exports one content asset as a Markdown file.

POST /exports/projects/{project_id}/bundle

Exports all content assets of one project as a Markdown bundle.

Current export directory:

backend/exports

The export directory is ignored by Git.

Current export format:

Markdown
    """,
)


append_once(
    "docs/project-status.md",
    "## Mega Pack C Completed",
    """
## Mega Pack C Completed

Name:

Export Layer

Added files:

- backend/src/services/export_service.py
- backend/src/api/exports.py
- backend/tests/smoke_test_exports.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md
- .gitignore

Added endpoints:

POST /exports/content-assets/{asset_id}/markdown

POST /exports/projects/{project_id}/bundle

Purpose:

Allow DAMA to produce usable Markdown files from stored content assets and projects.

Current export directory:

backend/exports

Next recommended Mega Pack:

Mega Pack D: Project-Aware Generation Batch

Suggested scope:

- batch generation request from project output plan
- create multiple generated assets in one call
- dry-run mode
- execution summary
- safer timeout handling
    """,
)

print("Mega Pack C applied successfully.")
