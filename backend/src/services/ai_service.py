from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from src.services.ollama_service import OllamaService
from src.services.prompt_service import PromptService


class AIServiceError(RuntimeError):
    """Base exception for AI service failures."""


class UnsupportedAIProviderError(AIServiceError):
    """Raised when the requested AI provider is not supported."""


class InvalidAIRequestError(AIServiceError):
    """Raised when an AI request is invalid."""


@dataclass(frozen=True, slots=True)
class AIProviderDefinition:
    """Supported AI provider metadata."""

    key: str
    label: str
    description: str
    supports_text_generation: bool
    supports_image_generation: bool
    is_local: bool

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "supports_text_generation": self.supports_text_generation,
            "supports_image_generation": self.supports_image_generation,
            "is_local": self.is_local,
        }


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

    SUPPORTED_PROVIDER_DEFINITIONS: ClassVar[tuple[AIProviderDefinition, ...]] = (
        AIProviderDefinition(
            key="ollama",
            label="Ollama",
            description="Local Ollama runtime for running local language models.",
            supports_text_generation=True,
            supports_image_generation=False,
            is_local=True,
        ),
    )

    SUPPORTED_PROVIDERS: ClassVar[frozenset[str]] = frozenset(
        provider.key for provider in SUPPORTED_PROVIDER_DEFINITIONS
    )

    @classmethod
    def list_providers(cls) -> list[dict[str, str | bool]]:
        """Return supported AI providers."""
        return [
            provider.to_dict()
            for provider in cls.SUPPORTED_PROVIDER_DEFINITIONS
        ]

    @classmethod
    def get_provider(cls, key: str) -> dict[str, str | bool]:
        """Return one supported AI provider by key."""
        provider_definition = cls._get_provider_definition(key)
        return provider_definition.to_dict()

    @classmethod
    def generate_text(
        cls,
        *,
        model: str,
        prompt: str | None = None,
        template: str | None = None,
        variables: dict[str, Any] | None = None,
        provider: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, str]:
        """
        Generate text using the selected AI provider.

        Supported input modes:
            - prompt
            - template + variables

        Currently supported providers:
            - ollama
        """
        final_prompt = cls._resolve_prompt(
            prompt=prompt,
            template=template,
            variables=variables,
        )

        request = cls._normalize_text_generation_request(
            model=model,
            prompt=final_prompt,
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
    def _resolve_prompt(
        cls,
        *,
        prompt: str | None,
        template: str | None,
        variables: dict[str, Any] | None,
    ) -> str:
        has_prompt = prompt is not None and bool(prompt.strip())
        has_template = template is not None and bool(template.strip())

        if has_prompt and has_template:
            raise InvalidAIRequestError(
                "Use either prompt or template, not both."
            )

        if has_prompt:
            return prompt.strip()

        if has_template:
            return PromptService.render_to_string(
                template=template or "",
                variables=variables or {},
            )

        raise InvalidAIRequestError(
            "Either prompt or template must be provided."
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

        cls._get_provider_definition(normalized_provider)

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

    @classmethod
    def _get_provider_definition(cls, key: str) -> AIProviderDefinition:
        normalized_key = key.strip().lower()

        if not normalized_key:
            raise UnsupportedAIProviderError("AI provider key cannot be empty.")

        for provider in cls.SUPPORTED_PROVIDER_DEFINITIONS:
            if provider.key == normalized_key:
                return provider

        raise UnsupportedAIProviderError(
            f"Unsupported AI provider: {normalized_key}"
        )
