from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import ContentAssetRepository
from src.repositories.project_repository import ProjectRepository
from src.services.project_service import InvalidProjectRequestError, ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectTypeResponse(BaseModel):
    key: str
    label: str
    description: str
    default_language: str
    default_content_types: list[str]
    workflow_stages: list[str]


class ProjectTypesResponse(BaseModel):
    project_types: list[ProjectTypeResponse]


class ProjectMetadataRequest(BaseModel):
    name: str = Field(..., min_length=1)
    project_type: str = Field(..., min_length=1)
    language: str | None = None
    description: str | None = None
    content_types: list[str] | None = None


class ProjectStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


class ProjectMetadataResponse(BaseModel):
    id: str
    name: str
    slug: str
    project_type: str
    language: str
    description: str | None
    status: str
    content_types: list[str]
    created_at: str
    updated_at: str


class ProjectsResponse(BaseModel):
    projects: list[ProjectMetadataResponse]


class ProjectContentAssetsResponse(BaseModel):
    project_id: str
    content_assets: list[dict[str, Any]]


class ProjectSummaryResponse(BaseModel):
    project: ProjectMetadataResponse
    total_assets: int
    assets_by_status: dict[str, int]
    assets_by_content_type: dict[str, int]


@router.get("/types", response_model=ProjectTypesResponse)
def list_project_types() -> dict[str, Any]:
    return {"project_types": ProjectService.list_project_types()}


@router.get("/types/{key}", response_model=ProjectTypeResponse)
def get_project_type(key: str) -> dict[str, Any]:
    try:
        return ProjectService.get_project_type(key)
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/metadata", response_model=ProjectMetadataResponse)
def build_project_metadata(request: ProjectMetadataRequest) -> dict[str, Any]:
    try:
        return ProjectService.build_project_metadata(
            name=request.name,
            project_type=request.project_type,
            language=request.language,
            description=request.description,
            content_types=request.content_types,
        )
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("", response_model=ProjectMetadataResponse, status_code=201)
def create_project(request: ProjectMetadataRequest) -> dict[str, Any]:
    try:
        project = ProjectService.build_project_metadata(
            name=request.name,
            project_type=request.project_type,
            language=request.language,
            description=request.description,
            content_types=request.content_types,
        )
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ProjectRepository()
    return repository.create_project(project)


@router.get("", response_model=ProjectsResponse)
def list_projects(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    repository = ProjectRepository()

    return {
        "projects": repository.list_projects(
            limit=limit,
            offset=offset,
        )
    }


@router.get("/{project_id}/content-assets", response_model=ProjectContentAssetsResponse)
def list_project_content_assets(project_id: str) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content_asset_repository = ContentAssetRepository()

    return {
        "project_id": project_id,
        "content_assets": content_asset_repository.list_content_assets(
            project_id=project_id,
        ),
    }


@router.get("/{project_id}/summary", response_model=ProjectSummaryResponse)
def get_project_summary(project_id: str) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content_asset_repository = ContentAssetRepository()
    content_assets = content_asset_repository.list_content_assets(project_id=project_id)

    status_counter = Counter(asset["status"] for asset in content_assets)
    content_type_counter = Counter(asset["content_type"] for asset in content_assets)

    return {
        "project": project,
        "total_assets": len(content_assets),
        "assets_by_status": dict(status_counter),
        "assets_by_content_type": dict(content_type_counter),
    }


@router.patch("/{project_id}/status", response_model=ProjectMetadataResponse)
def update_project_status(
    project_id: str,
    request: ProjectStatusRequest,
) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        normalized_status = ProjectService.normalize_status(request.status)
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated_project = project_repository.update_project_status(
        project_id=project_id,
        status=normalized_status,
        updated_at=datetime.now(UTC).isoformat(),
    )

    if updated_project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return updated_project


@router.get("/{project_id}", response_model=ProjectMetadataResponse)
def get_project(project_id: str) -> dict[str, Any]:
    repository = ProjectRepository()
    project = repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project
