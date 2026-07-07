from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status

from src.services.ai_service import AIService, UnsupportedAIProviderError


class AIProviderResponse(BaseModel):
    key: str
    label: str
    description: str
    supports_text_generation: bool
    supports_image_generation: bool
    is_local: bool


class AIProvidersResponse(BaseModel):
    providers: list[AIProviderResponse]


router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=AIProvidersResponse)
def list_providers() -> AIProvidersResponse:
    """
    Return supported AI providers.
    """
    return AIProvidersResponse(
        providers=AIService.list_providers()
    )


@router.get("/{key}", response_model=AIProviderResponse)
def get_provider(key: str) -> AIProviderResponse:
    """
    Return one supported AI provider by key.
    """
    try:
        provider = AIService.get_provider(key)
    except UnsupportedAIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AIProviderResponse(**provider)
