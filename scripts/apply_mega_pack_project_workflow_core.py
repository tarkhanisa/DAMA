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
    """,
)


write_file(
    "backend/src/repositories/project_repository.py",
    """
from __future__ import annotations

import json
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database


class ProjectRepositoryError(RuntimeError):
    pass


class ProjectRepository:
    def __init__(self) -> None:
        initialize_database()

    def create_project(self, project: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            connection.execute(
                '''
                INSERT INTO projects (
                    id,
                    name,
                    slug,
                    project_type,
                    language,
                    description,
                    status,
                    content_types,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    project["id"],
                    project["name"],
                    project["slug"],
                    project["project_type"],
                    project["language"],
                    project.get("description"),
                    project["status"],
                    json.dumps(project["content_types"], ensure_ascii=False),
                    project["created_at"],
                    project["updated_at"],
                ),
            )

        stored_project = self.get_project(project["id"])

        if stored_project is None:
            raise ProjectRepositoryError("Project was not stored correctly.")

        return stored_project

    def list_projects(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        with get_connection() as connection:
            rows = connection.execute(
                '''
                SELECT
                    id,
                    name,
                    slug,
                    project_type,
                    language,
                    description,
                    status,
                    content_types,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY created_at DESC
                LIMIT ?
                OFFSET ?
                ''',
                (safe_limit, safe_offset),
            ).fetchall()

        return [self._row_to_project(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                '''
                SELECT
                    id,
                    name,
                    slug,
                    project_type,
                    language,
                    description,
                    status,
                    content_types,
                    created_at,
                    updated_at
                FROM projects
                WHERE id = ?
                ''',
                (project_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_project(row)

    def update_project_status(
        self,
        *,
        project_id: str,
        status: str,
        updated_at: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            connection.execute(
                '''
                UPDATE projects
                SET status = ?, updated_at = ?
                WHERE id = ?
                ''',
                (status, updated_at, project_id),
            )

        return self.get_project(project_id)

    @staticmethod
    def _row_to_project(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "project_type": row["project_type"],
            "language": row["language"],
            "description": row["description"],
            "status": row["status"],
            "content_types": json.loads(row["content_types"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    """,
)


write_file(
    "backend/src/api/projects.py",
    """
from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import ContentAssetRepository
from src.repositories.project_repository import ProjectRepository
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


class ProjectStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


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


class ProjectsResponse(BaseModel):
    projects: list[ProjectMetadataResponse]


class ProjectContentAssetsResponse(BaseModel):
    project_id: str
    content_assets: list[dict[str, Any]]


class ProjectSummaryResponse(BaseModel):
    project: ProjectMetadataResponse
    total_assets: int
    assets_by_status: dict[str, int]
    assets_by_content_type: dict[str, int]


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


@router.post("", response_model=ProjectMetadataResponse, status_code=201)
def create_project(request: ProjectMetadataRequest) -> dict[str, Any]:
    try:
        project = ProjectService.build_project_metadata(
            name=request.name,
            project_type=request.project_type,
            language=request.language,
            description=request.description,
            content_types=request.content_types,
        )
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ProjectRepository()
    return repository.create_project(project)


@router.get("", response_model=ProjectsResponse)
def list_projects(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    repository = ProjectRepository()

    return {
        "projects": repository.list_projects(
            limit=limit,
            offset=offset,
        )
    }


@router.get("/{project_id}/content-assets", response_model=ProjectContentAssetsResponse)
def list_project_content_assets(project_id: str) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content_asset_repository = ContentAssetRepository()

    return {
        "project_id": project_id,
        "content_assets": content_asset_repository.list_content_assets(
            project_id=project_id,
        ),
    }


@router.get("/{project_id}/summary", response_model=ProjectSummaryResponse)
def get_project_summary(project_id: str) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content_asset_repository = ContentAssetRepository()
    content_assets = content_asset_repository.list_content_assets(project_id=project_id)

    status_counter = Counter(asset["status"] for asset in content_assets)
    content_type_counter = Counter(asset["content_type"] for asset in content_assets)

    return {
        "project": project,
        "total_assets": len(content_assets),
        "assets_by_status": dict(status_counter),
        "assets_by_content_type": dict(content_type_counter),
    }


@router.patch("/{project_id}/status", response_model=ProjectMetadataResponse)
def update_project_status(
    project_id: str,
    request: ProjectStatusRequest,
) -> dict[str, Any]:
    project_repository = ProjectRepository()
    project = project_repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        normalized_status = ProjectService.normalize_status(request.status)
    except InvalidProjectRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated_project = project_repository.update_project_status(
        project_id=project_id,
        status=normalized_status,
        updated_at=datetime.now(UTC).isoformat(),
    )

    if updated_project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return updated_project


@router.get("/{project_id}", response_model=ProjectMetadataResponse)
def get_project(project_id: str) -> dict[str, Any]:
    repository = ProjectRepository()
    project = repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project
    """,
)


write_file(
    "backend/src/api/content_generation.py",
    """
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

    response_text = str(generation_data.get("response", "")).strip()
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
    """,
)


write_file(
    "backend/tests/smoke_test_generation_storage.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app
from src.services.ollama_service import OllamaService


def main() -> None:
    print("DAMA generation storage smoke test started.")

    client = TestClient(app)

    models = OllamaService.list_models()
    assert models
    model_name = models[0].name

    project_name = f"DAMA Generation Storage Project {uuid4().hex[:8]}"

    print("Creating test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Project for generation storage smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]
    print("Test project created.")

    print("Checking POST /content/generate with save_output=true...")
    generation_response = client.post(
        "/content/generate",
        json={
            "model": model_name,
            "topic": "DAMA generation storage smoke test",
            "content_type": "social_caption",
            "instructions": "Reply with exactly this text: DAMA_GENERATION_STORAGE_OK",
            "project_id": project_id,
            "save_output": True,
            "asset_title": "Stored AI Generation Smoke Test",
            "asset_metadata": {
                "smoke_test": True,
            },
            "timeout": 120,
        },
    )
    assert generation_response.status_code == 200, generation_response.text

    generation = generation_response.json()
    assert "DAMA_GENERATION_STORAGE_OK" in generation["response"]
    assert generation["saved_content_asset"] is not None

    saved_asset = generation["saved_content_asset"]
    asset_id = saved_asset["id"]

    assert saved_asset["project_id"] == project_id
    assert saved_asset["source"] == "ai_generated"
    assert saved_asset["title"] == "Stored AI Generation Smoke Test"
    assert "DAMA_GENERATION_STORAGE_OK" in saved_asset["body"]
    assert saved_asset["metadata"]["smoke_test"] is True
    print("POST /content/generate with save_output=true OK.")

    print("Checking saved asset can be loaded...")
    asset_response = client.get(f"/content-assets/{asset_id}")
    assert asset_response.status_code == 200, asset_response.text
    loaded_asset = asset_response.json()
    assert loaded_asset["id"] == asset_id
    assert loaded_asset["project_id"] == project_id
    print("Saved asset load OK.")

    print("Checking project content assets include saved generation...")
    project_assets_response = client.get(f"/projects/{project_id}/content-assets")
    assert project_assets_response.status_code == 200, project_assets_response.text
    project_assets = project_assets_response.json()["content_assets"]
    assert any(asset["id"] == asset_id for asset in project_assets)
    print("Project content assets include saved generation OK.")

    print("Checking save_output=true without project_id...")
    invalid_response = client.post(
        "/content/generate",
        json={
            "model": model_name,
            "topic": "Invalid generation storage request",
            "content_type": "social_caption",
            "save_output": True,
            "timeout": 120,
        },
    )
    assert invalid_response.status_code == 400
    print("Missing project_id check OK.")

    print("DAMA generation storage smoke test passed.")


if __name__ == "__main__":
    main()
    """,
)


write_file(
    "backend/tests/smoke_test_project_workflow.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA project workflow smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Workflow Project {uuid4().hex[:8]}"

    print("Creating workflow project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Project workflow smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Workflow project created.")

    print("Creating draft content asset...")
    draft_asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Workflow Draft Asset",
            "body": "Workflow draft asset body.",
            "status": "draft",
        },
    )
    assert draft_asset_response.status_code == 201, draft_asset_response.text
    draft_asset_id = draft_asset_response.json()["id"]
    print("Draft content asset created.")

    print("Creating review content asset...")
    review_asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "social_caption",
            "title": "Workflow Review Asset",
            "body": "Workflow review asset body.",
            "status": "review",
        },
    )
    assert review_asset_response.status_code == 201, review_asset_response.text
    review_asset_id = review_asset_response.json()["id"]
    print("Review content asset created.")

    print("Checking GET /projects/{project_id}/content-assets...")
    project_assets_response = client.get(f"/projects/{project_id}/content-assets")
    assert project_assets_response.status_code == 200, project_assets_response.text
    project_assets = project_assets_response.json()["content_assets"]
    asset_ids = {asset["id"] for asset in project_assets}
    assert draft_asset_id in asset_ids
    assert review_asset_id in asset_ids
    print("GET /projects/{project_id}/content-assets OK.")

    print("Checking GET /projects/{project_id}/summary...")
    summary_response = client.get(f"/projects/{project_id}/summary")
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["project"]["id"] == project_id
    assert summary["total_assets"] >= 2
    assert summary["assets_by_status"]["draft"] >= 1
    assert summary["assets_by_status"]["review"] >= 1
    assert summary["assets_by_content_type"]["blog_post"] >= 1
    assert summary["assets_by_content_type"]["social_caption"] >= 1
    print("GET /projects/{project_id}/summary OK.")

    print("Checking PATCH /projects/{project_id}/status...")
    status_response = client.patch(
        f"/projects/{project_id}/status",
        json={
            "status": "active",
        },
    )
    assert status_response.status_code == 200, status_response.text
    updated_project = status_response.json()
    assert updated_project["status"] == "active"
    print("PATCH /projects/{project_id}/status OK.")

    print("Checking invalid project status...")
    invalid_status_response = client.patch(
        f"/projects/{project_id}/status",
        json={
            "status": "fake_status",
        },
    )
    assert invalid_status_response.status_code == 400
    print("Invalid project status check OK.")

    print("Checking missing project summary...")
    missing_summary_response = client.get("/projects/missing-project-id/summary")
    assert missing_summary_response.status_code == 404
    print("Missing project summary check OK.")

    print("DAMA project workflow smoke test passed.")


if __name__ == "__main__":
    main()
    """,
)


write_file(
    "scripts/backend-check.ps1",
    """
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\\backend\\.venv\\Scripts\\python.exe"
$AISmokeTestPath = ".\\backend\\tests\\smoke_test_ai.py"
$ProjectSmokeTestPath = ".\\backend\\tests\\smoke_test_projects.py"
$ContentAssetSmokeTestPath = ".\\backend\\tests\\smoke_test_content_assets.py"
$GenerationStorageSmokeTestPath = ".\\backend\\tests\\smoke_test_generation_storage.py"
$ProjectWorkflowSmokeTestPath = ".\\backend\\tests\\smoke_test_project_workflow.py"

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

if (-not (Test-Path $AISmokeTestPath)) {
    throw "AI smoke test was not found at $AISmokeTestPath"
}

if (-not (Test-Path $ProjectSmokeTestPath)) {
    throw "Project smoke test was not found at $ProjectSmokeTestPath"
}

if (-not (Test-Path $ContentAssetSmokeTestPath)) {
    throw "Content asset smoke test was not found at $ContentAssetSmokeTestPath"
}

if (-not (Test-Path $GenerationStorageSmokeTestPath)) {
    throw "Generation storage smoke test was not found at $GenerationStorageSmokeTestPath"
}

if (-not (Test-Path $ProjectWorkflowSmokeTestPath)) {
    throw "Project workflow smoke test was not found at $ProjectWorkflowSmokeTestPath"
}

Write-Host "Running DAMA backend AI smoke test..."
& $PythonPath $AISmokeTestPath

Write-Host ""
Write-Host "Running DAMA project persistence smoke test..."
& $PythonPath $ProjectSmokeTestPath

Write-Host ""
Write-Host "Running DAMA content asset smoke test..."
& $PythonPath $ContentAssetSmokeTestPath

Write-Host ""
Write-Host "Running DAMA generation storage smoke test..."
& $PythonPath $GenerationStorageSmokeTestPath

Write-Host ""
Write-Host "Running DAMA project workflow smoke test..."
& $PythonPath $ProjectWorkflowSmokeTestPath

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
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
                "description": "Structured content generation, content type catalog, and optional output storage.",
                "endpoints": [
                    "GET /content/types",
                    "GET /content/types/{key}",
                    "POST /content/generate",
                ],
            },
            "content_assets": {
                "description": "Persisted content assets connected to projects.",
                "endpoints": [
                    "POST /content-assets",
                    "GET /content-assets",
                    "GET /content-assets/{asset_id}",
                    "PATCH /content-assets/{asset_id}/status",
                ],
            },
            "providers": {
                "description": "AI provider catalog.",
                "endpoints": ["GET /providers", "GET /providers/{key}"],
            },
            "projects": {
                "description": "Project records, project workflow status, project content assets, and project summaries.",
                "endpoints": [
                    "GET /projects/types",
                    "GET /projects/types/{key}",
                    "POST /projects/metadata",
                    "POST /projects",
                    "GET /projects",
                    "GET /projects/{project_id}",
                    "GET /projects/{project_id}/content-assets",
                    "GET /projects/{project_id}/summary",
                    "PATCH /projects/{project_id}/status",
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
    "## Project Workflow Core",
    """
## Project Workflow Core

DAMA now supports project-level workflow operations.

Project workflow endpoints:

GET /projects/{project_id}/content-assets

Returns content assets connected to one project.

GET /projects/{project_id}/summary

Returns a project summary with:

- total_assets
- assets_by_status
- assets_by_content_type

PATCH /projects/{project_id}/status

Updates project workflow status.

Allowed project statuses:

- draft
- active
- review
- paused
- completed
- archived

## Generation Storage

POST /content/generate can optionally save generated output as a project-linked content asset.

Additional request fields:

project_id

Required when save_output is true.

save_output

Boolean. When true, generated content is stored as a content asset.

asset_title

Optional title for the saved content asset.

asset_status

Optional status for the saved content asset.

asset_metadata

Optional metadata dictionary for the saved content asset.

Current source value for saved generations:

ai_generated
    """,
)


append_once(
    "docs/project-status.md",
    "## Mega Pack A Completed",
    """
## Mega Pack A Completed

Name:

Project Workflow Core

Updated files:

- backend/src/services/project_service.py
- backend/src/repositories/project_repository.py
- backend/src/api/projects.py
- backend/src/api/content_generation.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added files:

- backend/tests/smoke_test_generation_storage.py
- backend/tests/smoke_test_project_workflow.py

Added behavior:

- POST /content/generate can save output into content assets
- GET /projects/{project_id}/content-assets
- GET /projects/{project_id}/summary
- PATCH /projects/{project_id}/status

Purpose:

Move DAMA from simple storage into project workflow core.

Next recommended Mega Pack:

Mega Pack B: Content Workflow Automation

Suggested scope:

- generate and save content through project-aware workflow endpoint
- create content asset drafts from project type defaults
- add project output plan endpoint
- add batch generation preparation
- avoid multi-agent logic for now
    """,
)

print("Mega Pack A applied successfully.")
