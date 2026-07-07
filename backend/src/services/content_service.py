from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.services.ai_service import AIService
from src.services.prompt_service import PromptService


class ContentServiceError(RuntimeError):
    """Base exception for content service failures."""


class InvalidContentRequestError(ContentServiceError):
    """Raised when a content generation request is invalid."""


@dataclass(frozen=True, slots=True)
class ContentGenerationRequest:
    """Normalized content generation request."""

    model: str
    topic: str
    content_type: str
    provider: str = "ollama"
    language: str = "English"
    tone: str = "professional"
    audience: str | None = None
    instructions: str | None = None
    timeout: int | None = None


@dataclass(frozen=True, slots=True)
class ContentGenerationResponse:
    """Generated content response."""

    provider: str
    model: str
    content_type: str
    topic: str
    language: str
    tone: str
    content: str
    prompt: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
            "content_type": self.content_type,
            "topic": self.topic,
            "language": self.language,
            "tone": self.tone,
            "content": self.content,
            "prompt": self.prompt,
        }


class ContentService:
    """High-level service for AI content generation."""

    DEFAULT_LANGUAGE = "English"
    DEFAULT_TONE = "professional"
    DEFAULT_PROVIDER = "ollama"

    CONTENT_PROMPT_TEMPLATE = """
You are DAMA, an AI content production assistant.

Generate {content_type} content.

Topic:
{topic}

Language:
{language}

Tone:
{tone}

Audience:
{audience}

Additional instructions:
{instructions}

Requirements:
- Produce only the requested content.
- Do not explain your process.
- Do not mention that you are an AI unless explicitly requested.
- Keep the output clean and ready to use.
""".strip()

    @classmethod
    def generate_content(
        cls,
        *,
        model: str,
        topic: str,
        content_type: str,
        provider: str | None = None,
        language: str | None = None,
        tone: str | None = None,
        audience: str | None = None,
        instructions: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, str]:
        """Generate production content using the configured AI provider."""
        request = cls._normalize_request(
            model=model,
            topic=topic,
            content_type=content_type,
            provider=provider,
            language=language,
            tone=tone,
            audience=audience,
            instructions=instructions,
            timeout=timeout,
        )

        prompt = cls.build_prompt(request)

        ai_result = AIService.generate_text(
            provider=request.provider,
            model=request.model,
            prompt=prompt,
            timeout=request.timeout,
        )

        response = ContentGenerationResponse(
            provider=ai_result["provider"],
            model=ai_result["model"],
            content_type=request.content_type,
            topic=request.topic,
            language=request.language,
            tone=request.tone,
            content=ai_result["response"],
            prompt=prompt,
        )

        return response.to_dict()

    @classmethod
    def build_prompt(cls, request: ContentGenerationRequest) -> str:
        """Build the final content prompt from a normalized request."""
        return PromptService.render_to_string(
            template=cls.CONTENT_PROMPT_TEMPLATE,
            variables={
                "content_type": request.content_type,
                "topic": request.topic,
                "language": request.language,
                "tone": request.tone,
                "audience": request.audience or "General audience",
                "instructions": request.instructions or "No additional instructions.",
            },
        )

    @classmethod
    def _normalize_request(
        cls,
        *,
        model: str,
        topic: str,
        content_type: str,
        provider: str | None,
        language: str | None,
        tone: str | None,
        audience: str | None,
        instructions: str | None,
        timeout: int | None,
    ) -> ContentGenerationRequest:
        normalized_model = model.strip()
        normalized_topic = topic.strip()
        normalized_content_type = content_type.strip()
        normalized_provider = (provider or cls.DEFAULT_PROVIDER).strip().lower()
        normalized_language = (language or cls.DEFAULT_LANGUAGE).strip()
        normalized_tone = (tone or cls.DEFAULT_TONE).strip()
        normalized_audience = audience.strip() if audience else None
        normalized_instructions = instructions.strip() if instructions else None

        if not normalized_model:
            raise InvalidContentRequestError("Model name cannot be empty.")

        if not normalized_topic:
            raise InvalidContentRequestError("Topic cannot be empty.")

        if not normalized_content_type:
            raise InvalidContentRequestError("Content type cannot be empty.")

        if not normalized_provider:
            raise InvalidContentRequestError("Provider cannot be empty.")

        if not normalized_language:
            raise InvalidContentRequestError("Language cannot be empty.")

        if not normalized_tone:
            raise InvalidContentRequestError("Tone cannot be empty.")

        if timeout is not None and timeout <= 0:
            raise InvalidContentRequestError("Timeout must be greater than zero.")

        return ContentGenerationRequest(
            provider=normalized_provider,
            model=normalized_model,
            topic=normalized_topic,
            content_type=normalized_content_type,
            language=normalized_language,
            tone=normalized_tone,
            audience=normalized_audience,
            instructions=normalized_instructions,
            timeout=timeout,
        )
