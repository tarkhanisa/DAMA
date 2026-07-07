from typing import Any

from pydantic import BaseModel
from fastapi import APIRouter

from src.services.system_service import SystemService


class OllamaStatusResponse(BaseModel):
    installed: bool
    version: str | None
    local_models_count: int


class SystemStatusResponse(BaseModel):
    app_name: str
    status: str
    ollama: OllamaStatusResponse
    providers_count: int
    content_types_count: int
    errors: list[str]


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status() -> dict[str, Any]:
    """
    Return DAMA backend runtime status.

    This endpoint aggregates real service checks:
    - application name
    - Ollama installation
    - Ollama version
    - local model count
    - provider count
    - content type count
    """
    return SystemService.get_status()
