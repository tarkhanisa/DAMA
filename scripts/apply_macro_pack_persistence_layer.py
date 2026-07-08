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
    '''
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
            """
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
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_projects_project_type
            ON projects(project_type)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_projects_status
            ON projects(status)
            """
        )
    ''',
)

write_file(
    "backend/src/repositories/__init__.py",
    '''
"""Repository package for DAMA."""
    ''',
)

write_file(
    "backend/src/repositories/project_repository.py",
    '''
from __future__ import annotations

import json
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database


class ProjectRepositoryError(RuntimeError):
    """Base exception for project repository failures."""


class ProjectRepository:
    """SQLite-backed project repository."""

    def __init__(self) -> None:
        initialize_database()

    def create_project(self, project: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            connection.execute(
                """
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
                """,
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
                """
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
                """,
                (safe_limit, safe_offset),
            ).fetchall()

        return [self._row_to_project(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
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
                """,
                (project_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_project(row)

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
    ''',
)

write_file(
    "backend/src/api/projects.py",
    '''
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

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


@router.get("/{project_id}", response_model=ProjectMetadataResponse)
def get_project(project_id: str) -> dict[str, Any]:
    repository = ProjectRepository()
    project = repository.get_project(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project
    ''',
)

write_file(
    "backend/tests/smoke_test_projects.py",
    '''
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA project persistence smoke test started.")

    client = TestClient(app)

    unique_name = f"DAMA Test Project {uuid4().hex[:8]}"

    print("Checking POST /projects...")
    create_response = client.post(
        "/projects",
        json={
            "name": unique_name,
            "project_type": "content_campaign",
            "description": "Persistent project smoke test.",
        },
    )
    assert create_response.status_code == 201, create_response.text

    created_project = create_response.json()
    assert created_project["name"] == unique_name
    assert created_project["project_type"] == "content_campaign"
    assert created_project["status"] == "draft"
    assert created_project["id"]

    project_id = created_project["id"]
    print("POST /projects OK.")

    print("Checking GET /projects/{project_id}...")
    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == 200, get_response.text
    loaded_project = get_response.json()
    assert loaded_project["id"] == project_id
    assert loaded_project["name"] == unique_name
    print("GET /projects/{project_id} OK.")

    print("Checking GET /projects...")
    list_response = client.get("/projects")
    assert list_response.status_code == 200, list_response.text
    projects = list_response.json()["projects"]
    assert any(project["id"] == project_id for project in projects)
    print("GET /projects OK.")

    print("Checking missing GET /projects/{project_id}...")
    missing_response = client.get("/projects/missing-project-id")
    assert missing_response.status_code == 404
    print("Missing project check OK.")

    print("Checking invalid POST /projects...")
    invalid_response = client.post(
        "/projects",
        json={
            "name": "Invalid Project",
            "project_type": "fake_type",
        },
    )
    assert invalid_response.status_code == 400
    print("Invalid project creation check OK.")

    print("DAMA project persistence smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)

write_file(
    "scripts/backend-check.ps1",
    '''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\\backend\\.venv\\Scripts\\python.exe"
$AISmokeTestPath = ".\\backend\\tests\\smoke_test_ai.py"
$ProjectSmokeTestPath = ".\\backend\\tests\\smoke_test_projects.py"

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

if (-not (Test-Path $AISmokeTestPath)) {
    throw "AI smoke test was not found at $AISmokeTestPath"
}

if (-not (Test-Path $ProjectSmokeTestPath)) {
    throw "Project smoke test was not found at $ProjectSmokeTestPath"
}

Write-Host "Running DAMA backend AI smoke test..."
& $PythonPath $AISmokeTestPath

Write-Host ""
Write-Host "Running DAMA project persistence smoke test..."
& $PythonPath $ProjectSmokeTestPath

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
    ''',
)

write_file(
    "backend/src/api/index.py",
    '''
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
    ''',
)

append_once(
    ".gitignore",
    "backend/data/*.db",
    '''
backend/data/*.db
backend/data/*.db-shm
backend/data/*.db-wal
    ''',
)

append_once(
    "docs/backend-api.md",
    "POST /projects",
    '''
## Persisted Projects API

POST /projects

Creates and stores a project record in the local DAMA database.

GET /projects

Returns stored project records.

GET /projects/{project_id}

Returns one stored project record by ID.

Current persistence backend:

SQLite through Python standard library.

Current database file:

backend/data/dama.db

The local database file is ignored by Git.
    ''',
)

append_once(
    "docs/project-status.md",
    "## Macro Pack 2 Completed",
    '''
## Macro Pack 2 Completed

Name:

Persistence Layer

Added files:

- backend/src/database/sqlite_database.py
- backend/src/repositories/__init__.py
- backend/src/repositories/project_repository.py
- backend/tests/smoke_test_projects.py

Updated files:

- backend/src/api/projects.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md
- .gitignore

Added endpoints:

POST /projects

GET /projects

GET /projects/{project_id}

Purpose:

Move DAMA from temporary project metadata generation to persisted project records.

Persistence backend:

SQLite standard library.

Database file:

backend/data/dama.db

Next recommended step:

Macro Pack 3: Content Asset Layer

Suggested scope:

- content asset model
- content repository
- project-to-content relationship
- generated content storage
- content list/read endpoints
- smoke test update
    ''',
)

print("Macro Pack 2 applied successfully.")
