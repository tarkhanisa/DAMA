from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4


class ProjectServiceError(RuntimeError):
    pass


class InvalidProjectRequestError(ProjectServiceError):
    pass


@dataclass(frozen=True, slots=True)
class ProjectTypeDefinition:
    key: str
    label: str
    description: str
    default_language: str
    default_content_types: tuple[str, ...]
    workflow_stages: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "default_language": self.default_language,
            "default_content_types": list(self.default_content_types),
            "workflow_stages": list(self.workflow_stages),
        }


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    id: str
    name: str
    slug: str
    project_type: str
    language: str
    description: str | None
    status: str
    content_types: tuple[str, ...]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "project_type": self.project_type,
            "language": self.language,
            "description": self.description,
            "status": self.status,
            "content_types": list(self.content_types),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ProjectService:
    DEFAULT_STATUS: ClassVar[str] = "draft"

    ALLOWED_STATUSES: ClassVar[set[str]] = {
        "draft",
        "active",
        "review",
        "paused",
        "completed",
        "archived",
    }

    SUPPORTED_PROJECT_TYPES: ClassVar[tuple[ProjectTypeDefinition, ...]] = (
        ProjectTypeDefinition(
            key="content_campaign",
            label="Content campaign",
            description="A structured campaign for producing multiple related content assets.",
            default_language="English",
            default_content_types=("blog_post", "social_caption", "email_campaign"),
            workflow_stages=("brief", "draft", "review", "approval", "publish"),
        ),
        ProjectTypeDefinition(
            key="product_launch",
            label="Product launch",
            description="A launch-oriented project for product copy, announcements, and social content.",
            default_language="English",
            default_content_types=(
                "product_description",
                "social_caption",
                "email_campaign",
                "press_release",
            ),
            workflow_stages=(
                "brief",
                "positioning",
                "content_generation",
                "review",
                "publish",
            ),
        ),
        ProjectTypeDefinition(
            key="video_package",
            label="Video package",
            description="A project for creating video scripts and supporting promotional content.",
            default_language="English",
            default_content_types=("video_script", "social_caption"),
            workflow_stages=("brief", "script", "review", "production", "publish"),
        ),
    )

    @classmethod
    def list_project_types(cls) -> list[dict[str, Any]]:
        return [project_type.to_dict() for project_type in cls.SUPPORTED_PROJECT_TYPES]

    @classmethod
    def get_project_type(cls, key: str) -> dict[str, Any]:
        return cls._get_project_type_definition(key).to_dict()

    @classmethod
    def build_project_metadata(
        cls,
        *,
        name: str,
        project_type: str,
        language: str | None = None,
        description: str | None = None,
        content_types: list[str] | tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        normalized_name = cls._normalize_required_text(name, "Project name")
        project_type_definition = cls._get_project_type_definition(project_type)

        normalized_language = (
            language.strip()
            if language and language.strip()
            else project_type_definition.default_language
        )

        normalized_description = (
            description.strip()
            if description and description.strip()
            else None
        )

        normalized_content_types = cls._normalize_content_types(
            content_types=content_types,
            fallback=project_type_definition.default_content_types,
        )

        now = datetime.now(UTC).isoformat()

        return ProjectMetadata(
            id=str(uuid4()),
            name=normalized_name,
            slug=cls._slugify(normalized_name),
            project_type=project_type_definition.key,
            language=normalized_language,
            description=normalized_description,
            status=cls.DEFAULT_STATUS,
            content_types=normalized_content_types,
            created_at=now,
            updated_at=now,
        ).to_dict()

    @classmethod
    def normalize_status(cls, status: str) -> str:
        normalized_status = cls._normalize_key(status, "Project status")

        if normalized_status not in cls.ALLOWED_STATUSES:
            raise InvalidProjectRequestError(
                f"Unsupported project status: {normalized_status}"
            )

        return normalized_status

    @classmethod
    def _get_project_type_definition(cls, key: str) -> ProjectTypeDefinition:
        normalized_key = cls._normalize_required_text(key, "Project type key").lower()

        for project_type in cls.SUPPORTED_PROJECT_TYPES:
            if project_type.key == normalized_key:
                return project_type

        raise InvalidProjectRequestError(f"Unsupported project type key: {normalized_key}")

    @classmethod
    def _normalize_content_types(
        cls,
        *,
        content_types: list[str] | tuple[str, ...] | None,
        fallback: tuple[str, ...],
    ) -> tuple[str, ...]:
        raw_content_types = content_types or fallback
        normalized_content_types: list[str] = []

        for content_type in raw_content_types:
            normalized_content_type = str(content_type).strip().lower()

            if not normalized_content_type:
                raise InvalidProjectRequestError("Content type cannot be empty.")

            if normalized_content_type not in normalized_content_types:
                normalized_content_types.append(normalized_content_type)

        if not normalized_content_types:
            raise InvalidProjectRequestError("At least one content type is required.")

        return tuple(normalized_content_types)

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise InvalidProjectRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @classmethod
    def _normalize_key(cls, value: str, field_name: str) -> str:
        normalized_value = cls._normalize_required_text(value, field_name).lower()
        normalized_value = re.sub(r"[^a-z0-9_]+", "_", normalized_value)
        normalized_value = normalized_value.strip("_")

        if not normalized_value:
            raise InvalidProjectRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @staticmethod
    def _slugify(value: str) -> str:
        normalized_value = value.strip().lower()
        normalized_value = re.sub(r"[^a-z0-9]+", "-", normalized_value)
        normalized_value = normalized_value.strip("-")

        if not normalized_value:
            return f"project-{uuid4().hex[:8]}"

        return normalized_value
