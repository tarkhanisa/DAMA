from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import (
    ContentAssetRepository,
    ContentAssetRepositoryError,
)
from src.services.content_asset_service import (
    ContentAssetService,
    InvalidContentAssetRequestError,
)


router = APIRouter(prefix="/content-assets", tags=["content-assets"])


class ContentAssetRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    status: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None


class ContentAssetStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


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


class ContentAssetsResponse(BaseModel):
    content_assets: list[ContentAssetResponse]


@router.post("", response_model=ContentAssetResponse, status_code=201)
def create_content_asset(request: ContentAssetRequest) -> dict[str, Any]:
    try:
        asset = ContentAssetService.build_content_asset(
            project_id=request.project_id,
            content_type=request.content_type,
            title=request.title,
            body=request.body,
            status=request.status,
            source=request.source,
            metadata=request.metadata,
        )
    except InvalidContentAssetRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ContentAssetRepository()

    try:
        return repository.create_content_asset(asset)
    except ContentAssetRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=ContentAssetsResponse)
def list_content_assets(
    project_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    repository = ContentAssetRepository()

    return {
        "content_assets": repository.list_content_assets(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
    }


@router.get("/{asset_id}", response_model=ContentAssetResponse)
def get_content_asset(asset_id: str) -> dict[str, Any]:
    repository = ContentAssetRepository()
    asset = repository.get_content_asset(asset_id)

    if asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    return asset


@router.patch("/{asset_id}/status", response_model=ContentAssetResponse)
def update_content_asset_status(
    asset_id: str,
    request: ContentAssetStatusRequest,
) -> dict[str, Any]:
    repository = ContentAssetRepository()
    current_asset = repository.get_content_asset(asset_id)

    if current_asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    try:
        updated_asset = ContentAssetService.update_status(
            current_asset=current_asset,
            status=request.status,
        )
    except InvalidContentAssetRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored_asset = repository.update_content_asset_status(
        asset_id=asset_id,
        status=updated_asset["status"],
        updated_at=updated_asset["updated_at"],
    )

    if stored_asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    return stored_asset
