from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from src.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"])


@router.get("/projects")
def search_projects(
    query: str | None = None,
    status: str | None = None,
    project_type: str | None = None,
    language: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return SearchService.search_projects(
        query=query,
        status=status,
        project_type=project_type,
        language=language,
        limit=limit,
        offset=offset,
    )


@router.get("/content-assets")
def search_content_assets(
    query: str | None = None,
    project_id: str | None = None,
    status: str | None = None,
    content_type: str | None = None,
    source: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return SearchService.search_content_assets(
        query=query,
        project_id=project_id,
        status=status,
        content_type=content_type,
        source=source,
        limit=limit,
        offset=offset,
    )
