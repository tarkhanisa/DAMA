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
    "backend/src/database/sqlite_database.py",
    """
from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def get_database_path() -> Path:
    configured_path = os.getenv("DAMA_DATABASE_PATH")

    if configured_path:
        return Path(configured_path)

    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "data" / "dama.db"


def get_connection() -> sqlite3.Connection:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                project_type TEXT NOT NULL,
                language TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                content_types TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            '''
        )

        connection.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_projects_project_type
            ON projects(project_type)
            '''
        )

        connection.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_projects_status
            ON projects(status)
            '''
        )

        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS content_assets (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            '''
        )

        connection.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_content_assets_project_id
            ON content_assets(project_id)
            '''
        )

        connection.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_content_assets_content_type
            ON content_assets(content_type)
            '''
        )

        connection.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_content_assets_status
            ON content_assets(status)
            '''
        )
    """,
)


write_file(
    "backend/src/services/content_asset_service.py",
    """
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4


class ContentAssetServiceError(RuntimeError):
    pass


class InvalidContentAssetRequestError(ContentAssetServiceError):
    pass


@dataclass(frozen=True, slots=True)
class ContentAsset:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "content_type": self.content_type,
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ContentAssetService:
    DEFAULT_STATUS: ClassVar[str] = "draft"
    DEFAULT_SOURCE: ClassVar[str] = "manual"

    ALLOWED_STATUSES: ClassVar[set[str]] = {
        "draft",
        "review",
        "approved",
        "published",
        "archived",
    }

    ALLOWED_SOURCES: ClassVar[set[str]] = {
        "manual",
        "ai_generated",
        "imported",
    }

    @classmethod
    def build_content_asset(
        cls,
        *,
        project_id: str,
        content_type: str,
        title: str,
        body: str,
        status: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_project_id = cls._normalize_required_text(project_id, "Project ID")
        normalized_content_type = cls._normalize_key(content_type, "Content type")
        normalized_title = cls._normalize_required_text(title, "Content title")
        normalized_body = cls._normalize_required_text(body, "Content body")
        normalized_status = cls._normalize_status(status or cls.DEFAULT_STATUS)
        normalized_source = cls._normalize_source(source or cls.DEFAULT_SOURCE)

        now = datetime.now(UTC).isoformat()

        asset = ContentAsset(
            id=str(uuid4()),
            project_id=normalized_project_id,
            content_type=normalized_content_type,
            title=normalized_title,
            body=normalized_body,
            status=normalized_status,
            source=normalized_source,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

        return asset.to_dict()

    @classmethod
    def update_status(
        cls,
        *,
        current_asset: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        normalized_status = cls._normalize_status(status)
        updated_asset = dict(current_asset)
        updated_asset["status"] = normalized_status
        updated_asset["updated_at"] = datetime.now(UTC).isoformat()

        return updated_asset

    @classmethod
    def _normalize_status(cls, status: str) -> str:
        normalized_status = cls._normalize_key(status, "Content asset status")

        if normalized_status not in cls.ALLOWED_STATUSES:
            raise InvalidContentAssetRequestError(
                f"Unsupported content asset status: {normalized_status}"
            )

        return normalized_status

    @classmethod
    def _normalize_source(cls, source: str) -> str:
        normalized_source = cls._normalize_key(source, "Content asset source")

        if normalized_source not in cls.ALLOWED_SOURCES:
            raise InvalidContentAssetRequestError(
                f"Unsupported content asset source: {normalized_source}"
            )

        return normalized_source

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise InvalidContentAssetRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @classmethod
    def _normalize_key(cls, value: str, field_name: str) -> str:
        normalized_value = cls._normalize_required_text(value, field_name).lower()
        normalized_value = re.sub(r"[^a-z0-9_]+", "_", normalized_value)
        normalized_value = normalized_value.strip("_")

        if not normalized_value:
            raise InvalidContentAssetRequestError(f"{field_name} cannot be empty.")

        return normalized_value
    """,
)


write_file(
    "backend/src/repositories/content_asset_repository.py",
    """
from __future__ import annotations

import json
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database


class ContentAssetRepositoryError(RuntimeError):
    pass


class ContentAssetRepository:
    def __init__(self) -> None:
        initialize_database()

    def create_content_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            existing_project = connection.execute(
                "SELECT id FROM projects WHERE id = ?",
                (asset["project_id"],),
            ).fetchone()

            if existing_project is None:
                raise ContentAssetRepositoryError("Project not found.")

            connection.execute(
                '''
                INSERT INTO content_assets (
                    id,
                    project_id,
                    content_type,
                    title,
                    body,
                    status,
                    source,
                    metadata,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    asset["id"],
                    asset["project_id"],
                    asset["content_type"],
                    asset["title"],
                    asset["body"],
                    asset["status"],
                    asset["source"],
                    json.dumps(asset["metadata"], ensure_ascii=False),
                    asset["created_at"],
                    asset["updated_at"],
                ),
            )

        stored_asset = self.get_content_asset(asset["id"])

        if stored_asset is None:
            raise ContentAssetRepositoryError("Content asset was not stored correctly.")

        return stored_asset

    def list_content_assets(
        self,
        *,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        with get_connection() as connection:
            if project_id:
                rows = connection.execute(
                    '''
                    SELECT
                        id,
                        project_id,
                        content_type,
                        title,
                        body,
                        status,
                        source,
                        metadata,
                        created_at,
                        updated_at
                    FROM content_assets
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    OFFSET ?
                    ''',
                    (project_id, safe_limit, safe_offset),
                ).fetchall()
            else:
                rows = connection.execute(
                    '''
                    SELECT
                        id,
                        project_id,
                        content_type,
                        title,
                        body,
                        status,
                        source,
                        metadata,
                        created_at,
                        updated_at
                    FROM content_assets
                    ORDER BY created_at DESC
                    LIMIT ?
                    OFFSET ?
                    ''',
                    (safe_limit, safe_offset),
                ).fetchall()

        return [self._row_to_asset(row) for row in rows]

    def get_content_asset(self, asset_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                '''
                SELECT
                    id,
                    project_id,
                    content_type,
                    title,
                    body,
                    status,
                    source,
                    metadata,
                    created_at,
                    updated_at
                FROM content_assets
                WHERE id = ?
                ''',
                (asset_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_asset(row)

    def update_content_asset_status(
        self,
        *,
        asset_id: str,
        status: str,
        updated_at: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            connection.execute(
                '''
                UPDATE content_assets
                SET status = ?, updated_at = ?
                WHERE id = ?
                ''',
                (status, updated_at, asset_id),
            )

        return self.get_content_asset(asset_id)

    @staticmethod
    def _row_to_asset(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "content_type": row["content_type"],
            "title": row["title"],
            "body": row["body"],
            "status": row["status"],
            "source": row["source"],
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    """,
)


write_file(
    "backend/src/api/content_assets.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import (
    ContentAssetRepository,
    ContentAssetRepositoryError,
)
from src.services.content_asset_service import (
    ContentAssetService,
    InvalidContentAssetRequestError,
)


router = APIRouter(prefix="/content-assets", tags=["content-assets"])


class ContentAssetRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    status: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None


class ContentAssetStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


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


class ContentAssetsResponse(BaseModel):
    content_assets: list[ContentAssetResponse]


@router.post("", response_model=ContentAssetResponse, status_code=201)
def create_content_asset(request: ContentAssetRequest) -> dict[str, Any]:
    try:
        asset = ContentAssetService.build_content_asset(
            project_id=request.project_id,
            content_type=request.content_type,
            title=request.title,
            body=request.body,
            status=request.status,
            source=request.source,
            metadata=request.metadata,
        )
    except InvalidContentAssetRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = ContentAssetRepository()

    try:
        return repository.create_content_asset(asset)
    except ContentAssetRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=ContentAssetsResponse)
def list_content_assets(
    project_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    repository = ContentAssetRepository()

    return {
        "content_assets": repository.list_content_assets(
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
    }


@router.get("/{asset_id}", response_model=ContentAssetResponse)
def get_content_asset(asset_id: str) -> dict[str, Any]:
    repository = ContentAssetRepository()
    asset = repository.get_content_asset(asset_id)

    if asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    return asset


@router.patch("/{asset_id}/status", response_model=ContentAssetResponse)
def update_content_asset_status(
    asset_id: str,
    request: ContentAssetStatusRequest,
) -> dict[str, Any]:
    repository = ContentAssetRepository()
    current_asset = repository.get_content_asset(asset_id)

    if current_asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    try:
        updated_asset = ContentAssetService.update_status(
            current_asset=current_asset,
            status=request.status,
        )
    except InvalidContentAssetRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored_asset = repository.update_content_asset_status(
        asset_id=asset_id,
        status=updated_asset["status"],
        updated_at=updated_asset["updated_at"],
    )

    if stored_asset is None:
        raise HTTPException(status_code=404, detail="Content asset not found.")

    return stored_asset
    """,
)


append_once(
    "backend/src/api/__init__.py",
    "content_assets_router",
    "from .content_assets import router as content_assets_router",
)

append_once(
    "backend/src/main.py",
    "content_assets_router",
    """
from src.api.content_assets import router as content_assets_router

app.include_router(content_assets_router)
    """,
)


write_file(
    "backend/tests/smoke_test_content_assets.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA content asset smoke test started.")

    client = TestClient(app)

    unique_name = f"DAMA Content Asset Project {uuid4().hex[:8]}"

    print("Creating test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": unique_name,
            "project_type": "content_campaign",
            "description": "Project for content asset smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Test project created.")

    print("Checking POST /content-assets...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "DAMA Test Blog Post",
            "body": "This is a persisted DAMA content asset.",
            "source": "manual",
            "metadata": {
                "test": True,
            },
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    asset = asset_response.json()
    assert asset["project_id"] == project_id
    assert asset["content_type"] == "blog_post"
    assert asset["status"] == "draft"
    asset_id = asset["id"]
    print("POST /content-assets OK.")

    print("Checking GET /content-assets/{asset_id}...")
    get_response = client.get(f"/content-assets/{asset_id}")
    assert get_response.status_code == 200, get_response.text
    loaded_asset = get_response.json()
    assert loaded_asset["id"] == asset_id
    assert loaded_asset["title"] == "DAMA Test Blog Post"
    print("GET /content-assets/{asset_id} OK.")

    print("Checking GET /content-assets...")
    list_response = client.get("/content-assets")
    assert list_response.status_code == 200, list_response.text
    assets = list_response.json()["content_assets"]
    assert any(item["id"] == asset_id for item in assets)
    print("GET /content-assets OK.")

    print("Checking GET /content-assets by project_id...")
    project_assets_response = client.get(f"/content-assets?project_id={project_id}")
    assert project_assets_response.status_code == 200, project_assets_response.text
    project_assets = project_assets_response.json()["content_assets"]
    assert any(item["id"] == asset_id for item in project_assets)
    print("GET /content-assets by project_id OK.")

    print("Checking PATCH /content-assets/{asset_id}/status...")
    status_response = client.patch(
        f"/content-assets/{asset_id}/status",
        json={
            "status": "review",
        },
    )
    assert status_response.status_code == 200, status_response.text
    updated_asset = status_response.json()
    assert updated_asset["status"] == "review"
    print("PATCH /content-assets/{asset_id}/status OK.")

    print("Checking invalid content asset project...")
    invalid_project_response = client.post(
        "/content-assets",
        json={
            "project_id": "missing-project-id",
            "content_type": "blog_post",
            "title": "Invalid Asset",
            "body": "Invalid asset body.",
        },
    )
    assert invalid_project_response.status_code == 404
    print("Invalid content asset project check OK.")

    print("Checking invalid content asset status...")
    invalid_status_response = client.patch(
        f"/content-assets/{asset_id}/status",
        json={
            "status": "fake_status",
        },
    )
    assert invalid_status_response.status_code == 400
    print("Invalid content asset status check OK.")

    print("DAMA content asset smoke test passed.")


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

Write-Host "Running DAMA backend AI smoke test..."
& $PythonPath $AISmokeTestPath

Write-Host ""
Write-Host "Running DAMA project persistence smoke test..."
& $PythonPath $ProjectSmokeTestPath

Write-Host ""
Write-Host "Running DAMA content asset smoke test..."
& $PythonPath $ContentAssetSmokeTestPath

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
                "description": "Structured content generation and content type catalog.",
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
                "description": "Project type catalog, project metadata preparation, and persisted project records.",
                "endpoints": [
                    "GET /projects/types",
                    "GET /projects/types/{key}",
                    "POST /projects/metadata",
                    "POST /projects",
                    "GET /projects",
                    "GET /projects/{project_id}",
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
    "## Content Assets API",
    """
## Content Assets API

The content asset API stores content outputs and connects them to projects.

POST /content-assets

Creates and stores a content asset.

GET /content-assets

Returns stored content assets.

GET /content-assets?project_id={project_id}

Returns content assets for one project.

GET /content-assets/{asset_id}

Returns one content asset by ID.

PATCH /content-assets/{asset_id}/status

Updates the content asset status.

Current content asset statuses:

- draft
- review
- approved
- published
- archived

Current content asset sources:

- manual
- ai_generated
- imported
    """,
)


append_once(
    "docs/project-status.md",
    "## Macro Pack 3 Completed",
    """
## Macro Pack 3 Completed

Name:

Content Asset Layer

Added files:

- backend/src/services/content_asset_service.py
- backend/src/repositories/content_asset_repository.py
- backend/src/api/content_assets.py
- backend/tests/smoke_test_content_assets.py

Updated files:

- backend/src/database/sqlite_database.py
- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

POST /content-assets

GET /content-assets

GET /content-assets?project_id={project_id}

GET /content-assets/{asset_id}

PATCH /content-assets/{asset_id}/status

Purpose:

Allow DAMA to store content outputs as project-linked assets.

Next recommended step:

Macro Pack 4: Generation History and Save Generated Output

Suggested scope:

- connect /content/generate to persisted content assets
- add optional project_id and save_output fields
- store AI-generated content as content asset
- add generation metadata
- update smoke tests
    """,
)

print("Macro Pack 3 applied successfully.")
