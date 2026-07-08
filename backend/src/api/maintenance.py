from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.maintenance_service import (
    MaintenanceService,
    MaintenanceServiceError,
)


router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/status")
def maintenance_status() -> dict[str, Any]:
    return MaintenanceService.get_status()


@router.post("/database/backup")
def backup_database() -> dict[str, Any]:
    try:
        return MaintenanceService.backup_database()
    except MaintenanceServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
