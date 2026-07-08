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
