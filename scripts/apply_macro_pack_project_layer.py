from pathlib import Path

ROOT = Path("I:/DAMA")

def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")

def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")

write_file(
    "backend/src/services/project_service.py",
    """
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4


class ProjectServiceError(RuntimeError):
    \"\"\"Base exception for project service failures.\"\"\"


class InvalidProjectRequestError(ProjectServiceError):
    \"\"\"Raised when a project request is invalid.\"\"\"


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

    @staticmethod
    def _slugify(value: str) -> str:
        normalized_value = value.strip().lower()
        normalized_value = re.sub(r"[^a-z0-9]+", "-", normalized_value)
        normalized_value = normalized_value.strip("-")

        if not normalized_value:
            return f"project-{uuid4().hex[:8]}"

        return normalized_value
    """,
)

write_file(
    "backend/src/api/projects.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.project_service import InvalidProjectRequestError, ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectTypeResponse(BaseModel):
    key: str
    label: str
    description: str
    default_language: str
    default_content_types: list[str]
    workflow_stages: list[str]


class ProjectTypesResponse(BaseModel):
    project_types: list[ProjectTypeResponse]


class ProjectMetadataRequest(BaseModel):
    name: str = Field(..., min_length=1)
    project_type: str = Field(..., min_length=1)
    language: str | None = None
    description: str | None = None
    content_types: list[str] | None = None


class ProjectMetadataResponse(BaseModel):
    id: str
    name: str
    slug: str
    project_type: str
    language: str
    description: str | None
    status: str
    content_types: list[str]
    created_at: str
    updated_at: str


@router.get("/types", response_model=ProjectTypesResponse)
def list_project_types() -> dict[str, Any]:
    return {"project_types": ProjectService.list_project_types()}


@router.get("/types/{key}", response_model=ProjectTypeResponse)
def get_project_type(key: str) -> dict[str, Any]:
    try:
        return ProjectService.get_project_type(key)
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/metadata", response_model=ProjectMetadataResponse)
def build_project_metadata(request: ProjectMetadataRequest) -> dict[str, Any]:
    try:
        return ProjectService.build_project_metadata(
            name=request.name,
            project_type=request.project_type,
            language=request.language,
            description=request.description,
            content_types=request.content_types,
        )
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    """,
)

append_once(
    "backend/src/api/__init__.py",
    "projects_router",
    "from .projects import router as projects_router",
)

append_once(
    "backend/src/main.py",
    "projects_router",
    """
from src.api.projects import router as projects_router

app.include_router(projects_router)
    """,
)

write_file(
    "backend/src/api/index.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter


router = APIRouter()


@router.get("/api")
def api_index() -> dict[str, Any]:
    return {
        "name": "DAMA Backend API",
        "version": "1.0.0",
        "description": "Backend API for the DAMA AI Content Automation Platform.",
        "capabilities": {
            "models": {
                "description": "Local AI model discovery.",
                "endpoints": ["GET /models"],
            },
            "generation": {
                "description": "Raw text generation through AI providers.",
                "endpoints": ["POST /generate"],
            },
            "content": {
                "description": "Structured content generation and content type catalog.",
                "endpoints": [
                    "GET /content/types",
                    "GET /content/types/{key}",
                    "POST /content/generate",
                ],
            },
            "providers": {
                "description": "AI provider catalog.",
                "endpoints": ["GET /providers", "GET /providers/{key}"],
            },
            "projects": {
                "description": "Project type catalog and project metadata preparation.",
                "endpoints": [
                    "GET /projects/types",
                    "GET /projects/types/{key}",
                    "POST /projects/metadata",
                ],
            },
            "system": {
                "description": "Runtime system status.",
                "endpoints": ["GET /system/status"],
            },
        },
    }
    """,
)

append_once(
    "docs/backend-api.md",
    "## Projects API",
    """
## Projects API

The project API prepares DAMA for project-based content workflows.

Current project endpoints:

GET /projects/types

GET /projects/types/{key}

POST /projects/metadata

Current supported project type keys:

- content_campaign
- product_launch
- video_package

Current note:

The project layer does not persist data yet. It prepares the future project record structure before database persistence is added.
    """,
)

append_once(
    "docs/project-status.md",
    "## Macro Pack 1 Completed",
    """
## Macro Pack 1 Completed

Name:

Project Layer without database persistence

Added files:

- backend/src/services/project_service.py
- backend/src/api/projects.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

GET /projects/types

GET /projects/types/{key}

POST /projects/metadata

Purpose:

Prepare DAMA for project-based content workflows before database persistence is added.

Next recommended step:

Macro Pack 2: Persistence Layer
    """,
)

print("Macro Pack 1 applied successfully.")
