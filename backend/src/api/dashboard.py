from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary() -> dict[str, Any]:
    return DashboardService.get_summary()
