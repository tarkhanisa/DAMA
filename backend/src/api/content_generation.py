from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import (
    ContentAssetRepository,
    ContentAssetRepositoryError,
)
from src.services.content_asset_service import (
    ContentAssetService,
    InvalidContentAssetRequestError,
)
from src.services.content_service import (
    ContentService,
    InvalidContentRequestError,
)


router = APIRouter(prefix="/content", tags=["content"])


class ContentTypeResponse(BaseModel):
    key: str
    label: str
    description: str
    default_tone: str
    default_instructions: str


class ContentTypesResponse(BaseModel):
    content_types: list[ContentTypeResponse]


class ContentAssetResponse(BaseModel):
    id: str
    project_id: str
    content_type: str
    title: str
    body: str
    status: str
    source: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class ContentGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    provider: str | None = None
    language: str | None = None
    tone: str | None = None
    audience: str | None = None
    instructions: str | None = None
    timeout: int | None = None

    project_id: str | None = None
    save_output: bool = False
    asset_title: str | None = None
    asset_status: str | None = None
    asset_metadata: dict[str, Any] | None = None


class ContentGenerateResponse(BaseModel):
    provider: str
    model: str
    topic: str
    content_type: str
    language: str | None
    tone: str | None
    audience: str | None
    instructions: str | None
    prompt: str
    response: str
    saved_content_asset: ContentAssetResponse | None = None


@router.get("/types", response_model=ContentTypesResponse)
def list_content_types() -> dict[str, Any]:
    return {
        "content_types": ContentService.list_content_types(),
    }


@router.get("/types/{key}", response_model=ContentTypeResponse)
def get_content_type(key: str) -> dict[str, Any]:
    try:
        return ContentService.get_content_type(key)
    except InvalidContentRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate", response_model=ContentGenerateResponse)
def generate_content(request: ContentGenerateRequest) -> dict[str, Any]:
    if request.save_output and not request.project_id:
        raise HTTPException(
            status_code=400,
            detail="project_id is required when save_output is true.",
        )

    try:
        generation_result = ContentService.generate_content(
            model=request.model,
            topic=request.topic,
            content_type=request.content_type,
            provider=request.provider,
            language=request.language,
            tone=request.tone,
            audience=request.audience,
            instructions=request.instructions,
            timeout=request.timeout,
        )
    except InvalidContentRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    generation_data = _to_dict(generation_result)

    response_text = _extract_generated_text(generation_data)

    if not response_text:
        raise HTTPException(status_code=502, detail="AI generation returned empty content.")
    prompt_text = str(generation_data.get("prompt", "")).strip()

    response_payload: dict[str, Any] = {
        "provider": str(generation_data.get("provider") or request.provider or "ollama"),
        "model": str(generation_data.get("model") or request.model),
        "topic": str(generation_data.get("topic") or request.topic),
        "content_type": str(generation_data.get("content_type") or request.content_type),
        "language": generation_data.get("language") or request.language,
        "tone": generation_data.get("tone") or request.tone,
        "audience": generation_data.get("audience") or request.audience,
        "instructions": generation_data.get("instructions") or request.instructions,
        "prompt": prompt_text,
        "response": response_text,
        "saved_content_asset": None,
    }

    if request.save_output:
        try:
            asset = ContentAssetService.build_content_asset(
                project_id=request.project_id or "",
                content_type=response_payload["content_type"],
                title=request.asset_title or _build_asset_title(
                    content_type=response_payload["content_type"],
                    topic=response_payload["topic"],
                ),
                body=response_payload["response"],
                status=request.asset_status,
                source="ai_generated",
                metadata=_build_asset_metadata(
                    request=request,
                    generation_data=generation_data,
                    extra_metadata=request.asset_metadata or {},
                ),
            )
        except InvalidContentAssetRequestError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        repository = ContentAssetRepository()

        try:
            response_payload["saved_content_asset"] = repository.create_content_asset(asset)
        except ContentAssetRepositoryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return response_payload


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    raise HTTPException(
        status_code=500,
        detail="Unsupported content generation result format.",
    )


def _build_asset_title(*, content_type: str, topic: str) -> str:
    clean_content_type = content_type.replace("_", " ").strip().title()
    clean_topic = topic.strip()

    return f"{clean_content_type}: {clean_topic}"


def _build_asset_metadata(
    *,
    request: ContentGenerateRequest,
    generation_data: dict[str, Any],
    extra_metadata: dict[str, Any],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "generator": "content_generate_endpoint",
        "provider": generation_data.get("provider") or request.provider or "ollama",
        "model": generation_data.get("model") or request.model,
        "topic": generation_data.get("topic") or request.topic,
        "content_type": generation_data.get("content_type") or request.content_type,
        "language": generation_data.get("language") or request.language,
        "tone": generation_data.get("tone") or request.tone,
        "audience": generation_data.get("audience") or request.audience,
        "instructions": generation_data.get("instructions") or request.instructions,
        "prompt": generation_data.get("prompt"),
    }

    metadata.update(extra_metadata)

    return metadata


def _extract_generated_text(generation_data: dict[str, Any]) -> str:
    possible_keys = [
        "response",
        "content",
        "body",
        "text",
        "output",
        "result",
        "generated_text",
        "generated_content",
    ]

    for key in possible_keys:
        value = generation_data.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    nested_generation = generation_data.get("generation")

    if isinstance(nested_generation, dict):
        for key in possible_keys:
            value = nested_generation.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

    nested_data = generation_data.get("data")

    if isinstance(nested_data, dict):
        for key in possible_keys:
            value = nested_data.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""

