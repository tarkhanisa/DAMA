from __future__ import annotations

import json
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database


class SearchServiceError(RuntimeError):
    pass


class SearchService:
    @classmethod
    def search_projects(
        cls,
        *,
        query: str | None = None,
        status: str | None = None,
        project_type: str | None = None,
        language: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        initialize_database()

        conditions: list[str] = []
        params: list[Any] = []

        if query and query.strip():
            like_query = f"%{query.strip().lower()}%"
            conditions.append(
                "(LOWER(name) LIKE ? OR LOWER(slug) LIKE ? OR LOWER(description) LIKE ?)"
            )
            params.extend([like_query, like_query, like_query])

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip())

        if project_type and project_type.strip():
            conditions.append("project_type = ?")
            params.append(project_type.strip())

        if language and language.strip():
            conditions.append("language = ?")
            params.append(language.strip())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        safe_limit = cls._normalize_limit(limit)
        safe_offset = cls._normalize_offset(offset)

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM projects {where_clause}",
                params,
            ).fetchone()["count"]

            rows = connection.execute(
                f"""
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
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, safe_limit, safe_offset],
            ).fetchall()

        return {
            "total": total,
            "limit": safe_limit,
            "offset": safe_offset,
            "items": [cls._project_row_to_dict(row) for row in rows],
        }

    @classmethod
    def search_content_assets(
        cls,
        *,
        query: str | None = None,
        project_id: str | None = None,
        status: str | None = None,
        content_type: str | None = None,
        source: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        initialize_database()

        conditions: list[str] = []
        params: list[Any] = []

        if query and query.strip():
            like_query = f"%{query.strip().lower()}%"
            conditions.append("(LOWER(title) LIKE ? OR LOWER(body) LIKE ?)")
            params.extend([like_query, like_query])

        if project_id and project_id.strip():
            conditions.append("project_id = ?")
            params.append(project_id.strip())

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip())

        if content_type and content_type.strip():
            conditions.append("content_type = ?")
            params.append(content_type.strip())

        if source and source.strip():
            conditions.append("source = ?")
            params.append(source.strip())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        safe_limit = cls._normalize_limit(limit)
        safe_offset = cls._normalize_offset(offset)

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM content_assets {where_clause}",
                params,
            ).fetchone()["count"]

            rows = connection.execute(
                f"""
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
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, safe_limit, safe_offset],
            ).fetchall()

        return {
            "total": total,
            "limit": safe_limit,
            "offset": safe_offset,
            "items": [cls._asset_row_to_dict(row) for row in rows],
        }

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        try:
            value = int(limit)
        except (TypeError, ValueError):
            value = 20

        return max(1, min(value, 100))

    @staticmethod
    def _normalize_offset(offset: int) -> int:
        try:
            value = int(offset)
        except (TypeError, ValueError):
            value = 0

        return max(0, value)

    @staticmethod
    def _loads_json(value: Any, fallback: Any) -> Any:
        if value is None:
            return fallback

        if isinstance(value, (list, dict)):
            return value

        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return fallback

    @classmethod
    def _project_row_to_dict(cls, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "project_type": row["project_type"],
            "language": row["language"],
            "description": row["description"],
            "status": row["status"],
            "content_types": cls._loads_json(row["content_types"], []),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @classmethod
    def _asset_row_to_dict(cls, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "content_type": row["content_type"],
            "title": row["title"],
            "body": row["body"],
            "status": row["status"],
            "source": row["source"],
            "metadata": cls._loads_json(row["metadata"], {}),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
