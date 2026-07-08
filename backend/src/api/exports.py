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
