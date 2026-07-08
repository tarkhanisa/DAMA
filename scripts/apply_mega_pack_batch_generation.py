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
    def build_batch_generation_plan(
        cls,
        *,
        project: dict[str, Any],
        topic: str | None = None,
        content_types: list[str] | None = None,
        max_outputs: int | None = None,
    ) -> list[dict[str, Any]]:
        plan = cls.build_output_plan(project=project, topic=topic)

        if content_types:
            requested_types = {
                cls._normalize_content_type(content_type)
                for content_type in content_types
            }

            plan = [
                item
                for item in plan
                if item["content_type"] in requested_types
            ]

        if not plan:
            raise InvalidWorkflowRequestError("No planned outputs matched the request.")

        if max_outputs is not None:
            if max_outputs < 1:
                raise InvalidWorkflowRequestError("max_outputs must be greater than zero.")

            plan = plan[:max_outputs]

        return plan

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

    @staticmethod
    def _normalize_content_type(content_type: str) -> str:
        normalized_content_type = str(content_type or "").strip().lower()

        if not normalized_content_type:
            raise InvalidWorkflowRequestError("Content type cannot be empty.")

        return normalized_content_type
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


class BatchGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    topic: str | None = None
    provider: str | None = None
    language: str | None = None
    tone: str | None = None
    audience: str | None = None
    instructions: str | None = None
    timeout: int | None = None
    content_types: list[str] | None = None
    max_outputs: int | None = Field(default=None, ge=1, le=10)
    dry_run: bool = True
    asset_status: str | None = None
    asset_metadata: dict[str, Any] | None = None


class BatchGenerateResponse(BaseModel):
    project_id: str
    dry_run: bool
    planned_count: int
    generated_count: int
    planned_outputs: list[PlannedOutputResponse]
    saved_content_assets: list[ContentAssetResponse]


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

    generation_data = _generate_content(
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

    response_text = str(generation_data.get("response", "")).strip()
    provider = str(generation_data.get("provider") or request.provider or "ollama")
    model = str(generation_data.get("model") or request.model)
    content_type = str(generation_data.get("content_type") or request.content_type)

    saved_asset = _save_generated_asset(
        project_id=project_id,
        content_type=content_type,
        title=request.asset_title or f"{project['name']} - {content_type.replace('_', ' ').title()}",
        body=response_text,
        status=request.asset_status,
        provider=provider,
        model=model,
        topic=topic,
        prompt=generation_data.get("prompt"),
        metadata={
            "workflow": "project_generate",
            **(request.asset_metadata or {}),
        },
    )

    return {
        "provider": provider,
        "model": model,
        "project_id": project_id,
        "topic": topic,
        "content_type": content_type,
        "response": response_text,
        "saved_content_asset": saved_asset,
    }


@router.post("/projects/{project_id}/batch-generate", response_model=BatchGenerateResponse)
def batch_generate_project_content(
    project_id: str,
    request: BatchGenerateRequest,
) -> dict[str, Any]:
    project = _load_project(project_id)

    try:
        planned_outputs = WorkflowService.build_batch_generation_plan(
            project=project,
            topic=request.topic,
            content_types=request.content_types,
            max_outputs=request.max_outputs,
        )
    except InvalidWorkflowRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if request.dry_run:
        return {
            "project_id": project_id,
            "dry_run": True,
            "planned_count": len(planned_outputs),
            "generated_count": 0,
            "planned_outputs": planned_outputs,
            "saved_content_assets": [],
        }

    saved_assets: list[dict[str, Any]] = []

    for item in planned_outputs:
        generation_data = _generate_content(
            model=request.model,
            topic=item["generation_topic"],
            content_type=item["content_type"],
            provider=request.provider,
            language=request.language or project.get("language"),
            tone=request.tone,
            audience=request.audience,
            instructions=request.instructions,
            timeout=request.timeout,
        )

        response_text = str(generation_data.get("response", "")).strip()
        provider = str(generation_data.get("provider") or request.provider or "ollama")
        model = str(generation_data.get("model") or request.model)

        saved_asset = _save_generated_asset(
            project_id=project_id,
            content_type=item["content_type"],
            title=item["title"],
            body=response_text,
            status=request.asset_status,
            provider=provider,
            model=model,
            topic=item["generation_topic"],
            prompt=generation_data.get("prompt"),
            metadata={
                "workflow": "project_batch_generate",
                "planned_order": item["order"],
                **(request.asset_metadata or {}),
            },
        )
        saved_assets.append(saved_asset)

    return {
        "project_id": project_id,
        "dry_run": False,
        "planned_count": len(planned_outputs),
        "generated_count": len(saved_assets),
        "planned_outputs": planned_outputs,
        "saved_content_assets": saved_assets,
    }


def _load_project(project_id: str) -> dict[str, Any]:
    repository = ProjectRepository()
    project = repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project


def _generate_content(
    *,
    model: str,
    topic: str,
    content_type: str,
    provider: str | None,
    language: str | None,
    tone: str | None,
    audience: str | None,
    instructions: str | None,
    timeout: int | None,
) -> dict[str, Any]:
    try:
        generation_result = ContentService.generate_content(
            model=model,
            topic=topic,
            content_type=content_type,
            provider=provider,
            language=language,
            tone=tone,
            audience=audience,
            instructions=instructions,
            timeout=timeout,
        )
    except InvalidContentRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _to_dict(generation_result)


def _save_generated_asset(
    *,
    project_id: str,
    content_type: str,
    title: str,
    body: str,
    status: str | None,
    provider: str,
    model: str,
    topic: str,
    prompt: Any,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    try:
        asset = ContentAssetService.build_content_asset(
            project_id=project_id,
            content_type=content_type,
            title=title,
            body=body,
            status=status,
            source="ai_generated",
            metadata={
                "provider": provider,
                "model": model,
                "topic": topic,
                "prompt": prompt,
                **metadata,
            },
        )
    except InvalidContentAssetRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ContentAssetRepository()

    try:
        return repository.create_content_asset(asset)
    except ContentAssetRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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


write_file(
    "backend/tests/smoke_test_batch_generation.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA batch generation smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Batch Generation {uuid4().hex[:8]}"

    print("Creating batch generation project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Batch generation smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]
    print("Project created.")

    print("Checking dry-run batch generation...")
    dry_run_response = client.post(
        f"/workflows/projects/{project_id}/batch-generate",
        json={
            "model": "dry-run-model",
            "topic": "DAMA batch generation dry run",
            "dry_run": True,
            "max_outputs": 2,
        },
    )
    assert dry_run_response.status_code == 200, dry_run_response.text
    dry_run = dry_run_response.json()
    assert dry_run["project_id"] == project_id
    assert dry_run["dry_run"] is True
    assert dry_run["planned_count"] == 2
    assert dry_run["generated_count"] == 0
    assert len(dry_run["planned_outputs"]) == 2
    assert dry_run["saved_content_assets"] == []
    print("Dry-run batch generation OK.")

    print("Checking dry-run content type filtering...")
    filtered_response = client.post(
        f"/workflows/projects/{project_id}/batch-generate",
        json={
            "model": "dry-run-model",
            "topic": "DAMA batch generation filtered dry run",
            "dry_run": True,
            "content_types": ["blog_post"],
        },
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered = filtered_response.json()
    assert filtered["planned_count"] == 1
    assert filtered["planned_outputs"][0]["content_type"] == "blog_post"
    print("Dry-run content type filtering OK.")

    print("Checking dry-run unmatched content type...")
    unmatched_response = client.post(
        f"/workflows/projects/{project_id}/batch-generate",
        json={
            "model": "dry-run-model",
            "topic": "DAMA unmatched dry run",
            "dry_run": True,
            "content_types": ["unknown_type"],
        },
    )
    assert unmatched_response.status_code == 400
    print("Unmatched content type check OK.")

    print("Checking missing project...")
    missing_response = client.post(
        "/workflows/projects/missing-project-id/batch-generate",
        json={
            "model": "dry-run-model",
            "dry_run": True,
        },
    )
    assert missing_response.status_code == 404
    print("Missing project check OK.")

    print("DAMA batch generation smoke test passed.")


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
    "## Batch Generation API",
    """
## Batch Generation API

The batch generation API prepares or executes multiple project-aware content generations.

POST /workflows/projects/{project_id}/batch-generate

Request fields:

model

Required model name.

topic

Optional generation topic. Defaults to project name.

content_types

Optional list of content types to generate.

max_outputs

Optional maximum number of planned outputs. Current accepted range: 1 to 10.

dry_run

Boolean. Defaults to true.

When dry_run is true:

- no AI generation is executed
- no content asset is created
- a planned output list is returned

When dry_run is false:

- each planned output is generated
- each generated result is stored as a content asset
- execution summary is returned

Recommended use:

Start with dry_run true, review planned outputs, then execute with dry_run false.
    """,
)


append_once(
    "docs/project-status.md",
    "## Mega Pack D Completed",
    """
## Mega Pack D Completed

Name:

Project-Aware Batch Generation

Updated files:

- backend/src/services/workflow_service.py
- backend/src/api/workflows.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added files:

- backend/tests/smoke_test_batch_generation.py

Added endpoint:

POST /workflows/projects/{project_id}/batch-generate

Added behavior:

- dry-run batch generation planning
- content type filtering
- max output limiting
- optional execution mode
- generated content asset storage when dry_run is false

Purpose:

Allow DAMA to prepare and eventually execute multiple project-aware content generations in one workflow call.

Next recommended Mega Pack:

Mega Pack E: Dashboard Readiness API

Suggested scope:

- aggregate dashboard summary endpoint
- counts for projects, assets, statuses, exports
- recent projects
- recent content assets
- system + workflow readiness summary
    """,
)

print("Mega Pack D applied successfully.")
