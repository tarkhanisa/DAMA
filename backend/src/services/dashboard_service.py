from __future__ import annotations

from pathlib import Path
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database
from src.services.system_service import SystemService


class DashboardServiceError(RuntimeError):
    pass


class DashboardService:
    @classmethod
    def get_summary(cls) -> dict[str, Any]:
        initialize_database()

        return {
            "system": SystemService.get_status(),
            "projects": cls._get_project_summary(),
            "content_assets": cls._get_content_asset_summary(),
            "exports": cls._get_export_summary(),
            "readiness": cls._get_readiness_summary(),
        }

    @classmethod
    def _get_project_summary(cls) -> dict[str, Any]:
        with get_connection() as connection:
            total_projects = connection.execute(
                "SELECT COUNT(*) AS count FROM projects"
            ).fetchone()["count"]

            projects_by_status_rows = connection.execute(
                '''
                SELECT status, COUNT(*) AS count
                FROM projects
                GROUP BY status
                ORDER BY status ASC
                '''
            ).fetchall()

            projects_by_type_rows = connection.execute(
                '''
                SELECT project_type, COUNT(*) AS count
                FROM projects
                GROUP BY project_type
                ORDER BY project_type ASC
                '''
            ).fetchall()

            recent_project_rows = connection.execute(
                '''
                SELECT
                    id,
                    name,
                    slug,
                    project_type,
                    language,
                    description,
                    status,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY created_at DESC
                LIMIT 5
                '''
            ).fetchall()

        return {
            "total": total_projects,
            "by_status": {
                row["status"]: row["count"]
                for row in projects_by_status_rows
            },
            "by_type": {
                row["project_type"]: row["count"]
                for row in projects_by_type_rows
            },
            "recent": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "project_type": row["project_type"],
                    "language": row["language"],
                    "description": row["description"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in recent_project_rows
            ],
        }

    @classmethod
    def _get_content_asset_summary(cls) -> dict[str, Any]:
        with get_connection() as connection:
            total_assets = connection.execute(
                "SELECT COUNT(*) AS count FROM content_assets"
            ).fetchone()["count"]

            assets_by_status_rows = connection.execute(
                '''
                SELECT status, COUNT(*) AS count
                FROM content_assets
                GROUP BY status
                ORDER BY status ASC
                '''
            ).fetchall()

            assets_by_type_rows = connection.execute(
                '''
                SELECT content_type, COUNT(*) AS count
                FROM content_assets
                GROUP BY content_type
                ORDER BY content_type ASC
                '''
            ).fetchall()

            assets_by_source_rows = connection.execute(
                '''
                SELECT source, COUNT(*) AS count
                FROM content_assets
                GROUP BY source
                ORDER BY source ASC
                '''
            ).fetchall()

            recent_asset_rows = connection.execute(
                '''
                SELECT
                    id,
                    project_id,
                    content_type,
                    title,
                    status,
                    source,
                    created_at,
                    updated_at
                FROM content_assets
                ORDER BY created_at DESC
                LIMIT 5
                '''
            ).fetchall()

        return {
            "total": total_assets,
            "by_status": {
                row["status"]: row["count"]
                for row in assets_by_status_rows
            },
            "by_content_type": {
                row["content_type"]: row["count"]
                for row in assets_by_type_rows
            },
            "by_source": {
                row["source"]: row["count"]
                for row in assets_by_source_rows
            },
            "recent": [
                {
                    "id": row["id"],
                    "project_id": row["project_id"],
                    "content_type": row["content_type"],
                    "title": row["title"],
                    "status": row["status"],
                    "source": row["source"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in recent_asset_rows
            ],
        }

    @staticmethod
    def _get_export_summary() -> dict[str, Any]:
        backend_root = Path(__file__).resolve().parents[2]
        export_root = backend_root / "exports"

        markdown_files = list(export_root.rglob("*.md")) if export_root.exists() else []

        recent_files = sorted(
            markdown_files,
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:5]

        return {
            "total_markdown_files": len(markdown_files),
            "export_root": str(export_root),
            "recent": [
                {
                    "file_name": item.name,
                    "file_path": str(item),
                    "size_bytes": item.stat().st_size,
                }
                for item in recent_files
            ],
        }

    @classmethod
    def _get_readiness_summary(cls) -> dict[str, Any]:
        project_summary = cls._get_project_summary()
        content_asset_summary = cls._get_content_asset_summary()
        export_summary = cls._get_export_summary()

        has_projects = project_summary["total"] > 0
        has_content_assets = content_asset_summary["total"] > 0
        has_exports = export_summary["total_markdown_files"] > 0

        return {
            "has_projects": has_projects,
            "has_content_assets": has_content_assets,
            "has_exports": has_exports,
            "dashboard_ready": True,
            "workflow_ready": has_projects and has_content_assets,
            "export_ready": has_content_assets,
        }
