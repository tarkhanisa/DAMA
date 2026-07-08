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
