from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.services.developer_service import DeveloperService


router = APIRouter(prefix="/developer", tags=["developer"])


@router.get("/endpoint-map")
def endpoint_map(request: Request) -> dict[str, Any]:
    return DeveloperService.get_endpoint_map(request.app)


@router.get("/frontend-contract")
def frontend_contract(request: Request) -> dict[str, Any]:
    return DeveloperService.get_frontend_contract(request.app)


@router.get("/runbook")
def runbook() -> dict[str, Any]:
    return DeveloperService.get_runbook()
