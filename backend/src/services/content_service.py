from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.services.ai_service import AIService
from src.services.prompt_service import PromptService


class ContentServiceError(RuntimeError):
    """Base exception for content service failures."""


class InvalidContentRequestError(ContentServiceError):
    """Raised when a content generation request is invalid."""


@dataclass(frozen=True, slots=True)
class ContentTypeDefinition:
    """Supported content type metadata."""

    key: str
    label: str
    description: str
    default_tone: str
    default_instructions: str

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "default_tone": self.default_tone,
            "default_instructions": self.default_instructions,
        }


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

    DEFAULT_LANGUAGE: ClassVar[str] = "English"
    DEFAULT_PROVIDER: ClassVar[str] = "ollama"

    SUPPORTED_CONTENT_TYPES: ClassVar[tuple[ContentTypeDefinition, ...]] = (
        ContentTypeDefinition(
            key="blog_post",
            label="Blog post",
            description="Long-form article or blog content.",
            default_tone="informative",
            default_instructions="Write a clear, structured blog post with a useful introduction and practical body.",
        ),
        ContentTypeDefinition(
            key="social_caption",
            label="Social caption",
            description="Short caption for social media posts.",
            default_tone="friendly",
            default_instructions="Write a concise social caption with a clear hook and natural call to action.",
        ),
        ContentTypeDefinition(
            key="product_description",
            label="Product description",
            description="Product-focused copy for ecommerce or catalog pages.",
            default_tone="persuasive",
            default_instructions="Write benefit-focused product copy that is clear, accurate, and ready to publish.",
        ),
        ContentTypeDefinition(
            key="video_script",
            label="Video script",
            description="Script for short videos, reels, explainers, or promotional clips.",
            default_tone="engaging",
            default_instructions="Write a structured video script with a hook, body, and closing line.",
        ),
        ContentTypeDefinition(
            key="email_campaign",
            label="Email campaign",
            description="Marketing or announcement email content.",
            default_tone="professional",
            default_instructions="Write a complete email with a strong opening, useful body, and clear call to action.",
        ),
        ContentTypeDefinition(
            key="press_release",
            label="Press release",
            description="Formal announcement for media or public communication.",
            default_tone="formal",
            default_instructions="Write a professional press release with a clear headline-style opening and factual structure.",
        ),
    )

    CONTENT_PROMPT_TEMPLATE: ClassVar[str] = """
You are DAMA, an AI content production assistant.

Generate content using the following production brief.

Content type key:
{content_type}

Content type label:
{content_type_label}

Content type description:
{content_type_description}

Topic:
{topic}

Language:
{language}

Tone:
{tone}

Audience:
{audience}

Instructions:
{instructions}

Requirements:
- Produce only the requested content.
- Do not explain your process.
- Do not mention that you are an AI unless explicitly requested.
- Keep the output clean and ready to use.
""".strip()

    @classmethod
    def list_content_types(cls) -> list[dict[str, str]]:
        """Return supported standard content types."""
        return [
            content_type.to_dict()
            for content_type in cls.SUPPORTED_CONTENT_TYPES
        ]

    @classmethod
    def get_content_type(cls, key: str) -> dict[str, str]:
        """Return a supported content type by key."""
        return cls._get_content_type_definition(key).to_dict()

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
        content_type_definition = cls._get_content_type_definition(
            request.content_type
        )

        return PromptService.render_to_string(
            template=cls.CONTENT_PROMPT_TEMPLATE,
            variables={
                "content_type": content_type_definition.key,
                "content_type_label": content_type_definition.label,
                "content_type_description": content_type_definition.description,
                "topic": request.topic,
                "language": request.language,
                "tone": request.tone,
                "audience": request.audience or "General audience",
                "instructions": request.instructions or content_type_definition.default_instructions,
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
        normalized_provider = (provider or cls.DEFAULT_PROVIDER).strip().lower()
        normalized_language = (language or cls.DEFAULT_LANGUAGE).strip()
        normalized_audience = audience.strip() if audience else None

        content_type_definition = cls._get_content_type_definition(content_type)
        normalized_content_type = content_type_definition.key

        normalized_tone = (
            tone.strip()
            if tone and tone.strip()
            else content_type_definition.default_tone
        )

        normalized_instructions = (
            instructions.strip()
            if instructions and instructions.strip()
            else content_type_definition.default_instructions
        )

        if not normalized_model:
            raise InvalidContentRequestError("Model name cannot be empty.")

        if not normalized_topic:
            raise InvalidContentRequestError("Topic cannot be empty.")

        if not normalized_provider:
            raise InvalidContentRequestError("Provider cannot be empty.")

        if not normalized_language:
            raise InvalidContentRequestError("Language cannot be empty.")

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

    @classmethod
    def _get_content_type_definition(cls, key: str) -> ContentTypeDefinition:
        normalized_key = key.strip().lower()

        if not normalized_key:
            raise InvalidContentRequestError("Content type key cannot be empty.")

        for content_type in cls.SUPPORTED_CONTENT_TYPES:
            if content_type.key == normalized_key:
                return content_type

        raise InvalidContentRequestError(
            f"Unsupported content type key: {normalized_key}"
        )
