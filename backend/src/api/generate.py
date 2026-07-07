from typing import Any

from pydantic import BaseModel, Field, model_validator
from fastapi import APIRouter, HTTPException, status

from src.services.ai_service import (
    AIService,
    InvalidAIRequestError,
    UnsupportedAIProviderError,
)
from src.services.ollama_service import (
    OllamaCommandError,
    OllamaNotInstalledError,
    OllamaServiceError,
)
from src.services.prompt_service import PromptServiceError


class GenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    prompt: str | None = Field(default=None, min_length=1)
    template: str | None = Field(default=None, min_length=1)
    variables: dict[str, Any] | None = Field(default=None)
    provider: str | None = Field(default="ollama", min_length=1)
    timeout: int | None = Field(default=None, ge=1, le=600)

    @model_validator(mode="after")
    def validate_prompt_input(self) -> "GenerateRequest":
        has_prompt = self.prompt is not None and bool(self.prompt.strip())
        has_template = self.template is not None and bool(self.template.strip())

        if has_prompt and has_template:
            raise ValueError("Use either prompt or template, not both.")

        if not has_prompt and not has_template:
            raise ValueError("Either prompt or template must be provided.")

        return self


class GenerateResponse(BaseModel):
    provider: str
    model: str
    response: str


router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenerateResponse)
def generate_text(request: GenerateRequest) -> GenerateResponse:
    """
    Generate text using the high-level AIService.

    Supports:
        - direct prompt
        - prompt template + variables
    """
    try:
        result = AIService.generate_text(
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            template=request.template,
            variables=request.variables,
            timeout=request.timeout,
        )
    except UnsupportedAIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidAIRequestError as exc:
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

    return GenerateResponse(**result)
