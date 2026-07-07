from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

from src.services.ai_service import UnsupportedAIProviderError
from src.services.content_service import (
    ContentService,
    ContentServiceError,
    InvalidContentRequestError,
)
from src.services.ollama_service import (
    OllamaCommandError,
    OllamaNotInstalledError,
    OllamaServiceError,
)
from src.services.prompt_service import PromptServiceError


class ContentGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    provider: str | None = Field(default="ollama", min_length=1)
    language: str | None = Field(default="English", min_length=1)
    tone: str | None = Field(default="professional", min_length=1)
    audience: str | None = Field(default=None)
    instructions: str | None = Field(default=None)
    timeout: int | None = Field(default=None, ge=1, le=600)


class ContentGenerateResponse(BaseModel):
    provider: str
    model: str
    content_type: str
    topic: str
    language: str
    tone: str
    content: str
    prompt: str


router = APIRouter(prefix="/content", tags=["content"])


@router.post("/generate", response_model=ContentGenerateResponse)
def generate_content(request: ContentGenerateRequest) -> ContentGenerateResponse:
    """
    Generate structured production content using ContentService.

    This route is for content-oriented generation, not raw prompt completion.
    """
    try:
        result = ContentService.generate_content(
            provider=request.provider,
            model=request.model,
            topic=request.topic,
            content_type=request.content_type,
            language=request.language,
            tone=request.tone,
            audience=request.audience,
            instructions=request.instructions,
            timeout=request.timeout,
        )
    except InvalidContentRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ContentServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UnsupportedAIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PromptServiceError as exc:
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

    return ContentGenerateResponse(**result)
