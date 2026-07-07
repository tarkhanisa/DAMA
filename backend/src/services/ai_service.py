from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.services.ollama_service import OllamaService


class AIServiceError(RuntimeError):
    """Base exception for AI service failures."""


class UnsupportedAIProviderError(AIServiceError):
    """Raised when the requested AI provider is not supported."""


@dataclass(frozen=True, slots=True)
class TextGenerationRequest:
    """Normalized text generation request for AI providers."""

    model: str
    prompt: str
    provider: str = "ollama"
    timeout: int | None = None


@dataclass(frozen=True, slots=True)
class TextGenerationResponse:
    """Normalized text generation response from AI providers."""

    provider: str
    model: str
    response: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
            "response": self.response,
        }


class AIService:
    """
    High-level AI service.

    This service is the provider-agnostic layer between API routes and concrete
    AI backends such as Ollama.
    """

    DEFAULT_PROVIDER: ClassVar[str] = "ollama"
    SUPPORTED_PROVIDERS: ClassVar[frozenset[str]] = frozenset({"ollama"})

    @classmethod
    def generate_text(
        cls,
        *,
        model: str,
        prompt: str,
        provider: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, str]:
        """
        Generate text using the selected AI provider.

        Currently supported providers:
            - ollama
        """
        request = cls._normalize_text_generation_request(
            model=model,
            prompt=prompt,
            provider=provider,
            timeout=timeout,
        )

        if request.provider == "ollama":
            result = OllamaService.generate(
                model=request.model,
                prompt=request.prompt,
                timeout=request.timeout,
            )

            response = TextGenerationResponse(
                provider=request.provider,
                model=result["model"],
                response=result["response"],
            )

            return response.to_dict()

        raise UnsupportedAIProviderError(
            f"Unsupported AI provider: {request.provider}"
        )

    @classmethod
    def _normalize_text_generation_request(
        cls,
        *,
        model: str,
        prompt: str,
        provider: str | None,
        timeout: int | None,
    ) -> TextGenerationRequest:
        normalized_provider = (provider or cls.DEFAULT_PROVIDER).strip().lower()
        normalized_model = model.strip()
        normalized_prompt = prompt.strip()

        if normalized_provider not in cls.SUPPORTED_PROVIDERS:
            raise UnsupportedAIProviderError(
                f"Unsupported AI provider: {normalized_provider}"
            )

        if not normalized_model:
            raise ValueError("Model name cannot be empty.")

        if not normalized_prompt:
            raise ValueError("Prompt cannot be empty.")

        if timeout is not None and timeout <= 0:
            raise ValueError("Timeout must be greater than zero.")

        return TextGenerationRequest(
            provider=normalized_provider,
            model=normalized_model,
            prompt=normalized_prompt,
            timeout=timeout,
        )
