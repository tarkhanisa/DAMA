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
    "backend/src/services/workflow_service.py",
    """
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class WorkflowServiceError(RuntimeError):
    pass


class InvalidWorkflowRequestError(WorkflowServiceError):
    pass


@dataclass(frozen=True, slots=True)
class PlannedOutput:
    order: int
    project_id: str
    content_type: str
    title: str
    workflow_stage: str
    recommended_status: str
    generation_topic: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "project_id": self.project_id,
            "content_type": self.content_type,
            "title": self.title,
            "workflow_stage": self.workflow_stage,
            "recommended_status": self.recommended_status,
            "generation_topic": self.generation_topic,
        }


class WorkflowService:
    @classmethod
    def build_output_plan(
        cls,
        *,
        project: dict[str, Any],
        topic: str | None = None,
    ) -> list[dict[str, Any]]:
        project_id = cls._required(project.get("id"), "Project ID")
        project_name = cls._required(project.get("name"), "Project name")
        content_types = project.get("content_types") or []

        if not content_types:
            raise InvalidWorkflowRequestError("Project has no content types.")

        generation_topic = topic.strip() if topic and topic.strip() else project_name

        planned_outputs: list[PlannedOutput] = []

        for index, content_type in enumerate(content_types, start=1):
            normalized_content_type = cls._required(str(content_type), "Content type")
            title = f"{project_name} - {cls._humanize_content_type(normalized_content_type)}"

            planned_outputs.append(
                PlannedOutput(
                    order=index,
                    project_id=project_id,
                    content_type=normalized_content_type,
                    title=title,
                    workflow_stage="draft",
                    recommended_status="draft",
                    generation_topic=generation_topic,
                )
            )

        return [planned_output.to_dict() for planned_output in planned_outputs]

    @classmethod
    def build_draft_asset_payloads(
        cls,
        *,
        project: dict[str, Any],
        topic: str | None = None,
        title_prefix: str | None = None,
    ) -> list[dict[str, Any]]:
        plan = cls.build_output_plan(project=project, topic=topic)
        project_name = cls._required(project.get("name"), "Project name")
        clean_prefix = title_prefix.strip() if title_prefix and title_prefix.strip() else project_name

        payloads: list[dict[str, Any]] = []

        for item in plan:
            content_type = item["content_type"]
            title = f"{clean_prefix} - {cls._humanize_content_type(content_type)}"
            body = (
                f"Workflow draft for {cls._humanize_content_type(content_type)}. "
                f"Project: {project_name}. "
                f"Topic: {item['generation_topic']}. "
                "This asset is ready for AI generation or manual writing."
            )

            payloads.append(
                {
                    "project_id": item["project_id"],
                    "content_type": content_type,
                    "title": title,
                    "body": body,
                    "status": "draft",
                    "source": "manual",
                    "metadata": {
                        "workflow": "draft_asset_generation",
                        "planned_order": item["order"],
                        "generation_topic": item["generation_topic"],
                    },
                }
            )

        return payloads

    @staticmethod
    def _required(value: Any, field_name: str) -> str:
        normalized_value = str(value or "").strip()

        if not normalized_value:
            raise InvalidWorkflowRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @staticmethod
    def _humanize_content_type(content_type: str) -> str:
        return content_type.replace("_", " ").strip().title()
    """,
)


write_file(
    "backend/src/api/workflows.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import (
    ContentAssetRepository,
    ContentAssetRepositoryError,
)
from src.repositories.project_repository import ProjectRepository
from src.services.content_asset_service import (
    ContentAssetService,
    InvalidContentAssetRequestError,
)
from src.services.content_service import ContentService, InvalidContentRequestError
from src.services.workflow_service import InvalidWorkflowRequestError, WorkflowService


router = APIRouter(prefix="/workflows", tags=["workflows"])


class OutputPlanRequest(BaseModel):
    topic: str | None = None


class PlannedOutputResponse(BaseModel):
    order: int
    project_id: str
    content_type: str
    title: str
    workflow_stage: str
    recommended_status: str
    generation_topic: str


class OutputPlanResponse(BaseModel):
    project_id: str
    planned_outputs: list[PlannedOutputResponse]


class DraftAssetsRequest(BaseModel):
    topic: str | None = None
    title_prefix: str | None = None


class ContentAssetResponse(BaseModel):
    id: str
    project_id: str
    content_type: str
    title: str
    body: str
    status: str
    source: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class DraftAssetsResponse(BaseModel):
    project_id: str
    created_assets: list[ContentAssetResponse]


class WorkflowGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    topic: str | None = None
    provider: str | None = None
    language: str | None = None
    tone: str | None = None
    audience: str | None = None
    instructions: str | None = None
    timeout: int | None = None
    asset_title: str | None = None
    asset_status: str | None = None
    asset_metadata: dict[str, Any] | None = None


class WorkflowGenerateResponse(BaseModel):
    provider: str
    model: str
    project_id: str
    topic: str
    content_type: str
    response: str
    saved_content_asset: ContentAssetResponse


@router.get("/projects/{project_id}/output-plan", response_model=OutputPlanResponse)
def get_project_output_plan(project_id: str, topic: str | None = None) -> dict[str, Any]:
    project = _load_project(project_id)

    try:
        planned_outputs = WorkflowService.build_output_plan(
            project=project,
            topic=topic,
        )
    except InvalidWorkflowRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "project_id": project_id,
        "planned_outputs": planned_outputs,
    }


@router.post("/projects/{project_id}/draft-assets", response_model=DraftAssetsResponse)
def create_project_draft_assets(
    project_id: str,
    request: DraftAssetsRequest,
) -> dict[str, Any]:
    project = _load_project(project_id)

    try:
        payloads = WorkflowService.build_draft_asset_payloads(
            project=project,
            topic=request.topic,
            title_prefix=request.title_prefix,
        )
    except InvalidWorkflowRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ContentAssetRepository()
    created_assets: list[dict[str, Any]] = []

    for payload in payloads:
        try:
            asset = ContentAssetService.build_content_asset(**payload)
            created_assets.append(repository.create_content_asset(asset))
        except InvalidContentAssetRequestError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ContentAssetRepositoryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "project_id": project_id,
        "created_assets": created_assets,
    }


@router.post("/projects/{project_id}/generate", response_model=WorkflowGenerateResponse)
def generate_project_content(
    project_id: str,
    request: WorkflowGenerateRequest,
) -> dict[str, Any]:
    project = _load_project(project_id)

    topic = request.topic.strip() if request.topic and request.topic.strip() else project["name"]

    try:
        generation_result = ContentService.generate_content(
            model=request.model,
            topic=topic,
            content_type=request.content_type,
            provider=request.provider,
            language=request.language or project.get("language"),
            tone=request.tone,
            audience=request.audience,
            instructions=request.instructions,
            timeout=request.timeout,
        )
    except InvalidContentRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    generation_data = _to_dict(generation_result)

    response_text = str(generation_data.get("response", "")).strip()
    provider = str(generation_data.get("provider") or request.provider or "ollama")
    model = str(generation_data.get("model") or request.model)
    content_type = str(generation_data.get("content_type") or request.content_type)

    try:
        asset = ContentAssetService.build_content_asset(
            project_id=project_id,
            content_type=content_type,
            title=request.asset_title or f"{project['name']} - {content_type.replace('_', ' ').title()}",
            body=response_text,
            status=request.asset_status,
            source="ai_generated",
            metadata={
                "workflow": "project_generate",
                "provider": provider,
                "model": model,
                "topic": topic,
                "prompt": generation_data.get("prompt"),
                **(request.asset_metadata or {}),
            },
        )
    except InvalidContentAssetRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ContentAssetRepository()

    try:
        saved_asset = repository.create_content_asset(asset)
    except ContentAssetRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "provider": provider,
        "model": model,
        "project_id": project_id,
        "topic": topic,
        "content_type": content_type,
        "response": response_text,
        "saved_content_asset": saved_asset,
    }


def _load_project(project_id: str) -> dict[str, Any]:
    repository = ProjectRepository()
    project = repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    raise HTTPException(
        status_code=500,
        detail="Unsupported content generation result format.",
    )
    """,
)


append_once(
    "backend/src/api/__init__.py",
    "workflows_router",
    "from .workflows import router as workflows_router",
)

append_once(
    "backend/src/main.py",
    "workflows_router",
    """
from src.api.workflows import router as workflows_router

app.include_router(workflows_router)
    """,
)


write_file(
    "backend/tests/smoke_test_workflow_automation.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA workflow automation smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Workflow Automation {uuid4().hex[:8]}"

    print("Creating workflow automation project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Workflow automation smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Checking GET /workflows/projects/{project_id}/output-plan...")
    plan_response = client.get(
        f"/workflows/projects/{project_id}/output-plan",
        params={
            "topic": "DAMA workflow automation",
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    plan = plan_response.json()
    assert plan["project_id"] == project_id
    assert plan["planned_outputs"]
    assert any(item["content_type"] == "blog_post" for item in plan["planned_outputs"])
    print("Output plan OK.")

    print("Checking POST /workflows/projects/{project_id}/draft-assets...")
    draft_response = client.post(
        f"/workflows/projects/{project_id}/draft-assets",
        json={
            "topic": "DAMA workflow automation",
            "title_prefix": "Workflow Automation",
        },
    )
    assert draft_response.status_code == 200, draft_response.text
    draft_data = draft_response.json()
    created_assets = draft_data["created_assets"]
    assert created_assets
    assert all(asset["project_id"] == project_id for asset in created_assets)
    print("Draft assets OK.")

    print("Checking project summary after draft assets...")
    summary_response = client.get(f"/projects/{project_id}/summary")
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["total_assets"] >= len(created_assets)
    assert summary["assets_by_status"]["draft"] >= len(created_assets)
    print("Project summary after draft assets OK.")

    print("Checking missing workflow project...")
    missing_response = client.get("/workflows/projects/missing-project-id/output-plan")
    assert missing_response.status_code == 404
    print("Missing workflow project check OK.")

    print("DAMA workflow automation smoke test passed.")


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
    "docs/backend-api.md",
    "## Workflow Automation API",
    """
## Workflow Automation API

The workflow automation API adds project-aware content planning and content asset preparation.

GET /workflows/projects/{project_id}/output-plan

Returns a planned content output list based on the project content types.

Query fields:

topic

Optional. Overrides the default generation topic.

POST /workflows/projects/{project_id}/draft-assets

Creates draft content assets based on the project content types.

Request fields:

topic

Optional. Used as the workflow topic.

title_prefix

Optional. Used as the title prefix for created draft assets.

POST /workflows/projects/{project_id}/generate

Generates content for a project and stores the output as a content asset.

Current note:

The workflow automation layer is intentionally simple. It does not use multi-agent execution yet.
    """,
)


append_once(
    "docs/project-status.md",
    "## Mega Pack B Completed",
    """
## Mega Pack B Completed

Name:

Content Workflow Automation

Added files:

- backend/src/services/workflow_service.py
- backend/src/api/workflows.py
- backend/tests/smoke_test_workflow_automation.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

GET /workflows/projects/{project_id}/output-plan

POST /workflows/projects/{project_id}/draft-assets

POST /workflows/projects/{project_id}/generate

Purpose:

Move DAMA from project workflow storage to project-aware content workflow automation.

Next recommended Mega Pack:

Mega Pack C: Export Layer

Suggested scope:

- export content asset as markdown
- export project content bundle
- add local export directory
- add export repository/service
- add smoke test
    """,
)

print("Mega Pack B applied successfully.")
