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
