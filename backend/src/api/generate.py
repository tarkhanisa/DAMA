from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

from src.services.ai_service import AIService, UnsupportedAIProviderError
from src.services.ollama_service import (
    OllamaCommandError,
    OllamaNotInstalledError,
    OllamaServiceError,
)


class GenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    provider: str | None = Field(default="ollama", min_length=1)
    timeout: int | None = Field(default=None, ge=1, le=600)


class GenerateResponse(BaseModel):
    provider: str
    model: str
    response: str


router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenerateResponse)
def generate_text(request: GenerateRequest) -> GenerateResponse:
    """
    Generate text using the high-level AIService.

    The API route does not talk directly to concrete model providers.
    Provider-specific logic belongs in service layers.
    """
    try:
        result = AIService.generate_text(
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            timeout=request.timeout,
        )
    except UnsupportedAIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OllamaNotInstalledError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not installed or is not available in PATH.",
        ) from exc
    except OllamaCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": str(exc),
                "returncode": exc.returncode,
                "stderr": exc.stderr,
            },
        ) from exc
    except OllamaServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return GenerateResponse(**result)
