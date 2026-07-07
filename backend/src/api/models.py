from fastapi import APIRouter, HTTPException, status

from src.services.ollama_service import (
    OllamaNotInstalledError,
    OllamaService,
    OllamaServiceError,
)

router = APIRouter(tags=["models"])


@router.get("/models")
async def list_models() -> dict[str, list[dict[str, str | None]]]:
    """
    Return locally available Ollama models.

    This endpoint reads real local Ollama state using OllamaService.
    """
    try:
        models = OllamaService.list_models()
    except OllamaNotInstalledError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not installed or is not available in PATH.",
        ) from exc
    except OllamaServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {"models": models}
