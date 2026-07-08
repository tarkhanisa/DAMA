from __future__ import annotations

import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.database.sqlite_database import get_database_path, initialize_database


class MaintenanceServiceError(RuntimeError):
    pass


class MaintenanceService:
    @classmethod
    def get_status(cls) -> dict[str, Any]:
        initialize_database()

        database_path = get_database_path()
        backend_root = Path(__file__).resolve().parents[2]
        export_root = backend_root / "exports"
        backup_root = backend_root / "backups"

        return {
            "database": cls._get_database_status(database_path),
            "exports": cls._get_directory_status(export_root, pattern="*.md"),
            "backups": cls._get_directory_status(backup_root, pattern="*.db"),
            "maintenance_ready": True,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def backup_database(cls) -> dict[str, Any]:
        initialize_database()

        database_path = get_database_path()

        if not database_path.exists():
            raise MaintenanceServiceError("Database file does not exist.")

        backend_root = Path(__file__).resolve().parents[2]
        backup_root = backend_root / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_file = backup_root / f"dama-{timestamp}.db"

        shutil.copy2(database_path, backup_file)

        return {
            "backup_created": True,
            "source_path": str(database_path),
            "backup_path": str(backup_file),
            "size_bytes": backup_file.stat().st_size,
            "created_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def _get_database_status(cls, database_path: Path) -> dict[str, Any]:
        database_exists = database_path.exists()

        status: dict[str, Any] = {
            "path": str(database_path),
            "exists": database_exists,
            "size_bytes": database_path.stat().st_size if database_exists else 0,
            "tables": {},
        }

        if not database_exists:
            return status

        try:
            with sqlite3.connect(database_path) as connection:
                connection.row_factory = sqlite3.Row

                table_rows = connection.execute(
                    '''
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    ORDER BY name ASC
                    '''
                ).fetchall()

                for row in table_rows:
                    table_name = row["name"]

                    if table_name.startswith("sqlite_"):
                        continue

                    count_row = connection.execute(
                        f"SELECT COUNT(*) AS count FROM {table_name}"
                    ).fetchone()

                    status["tables"][table_name] = count_row["count"]
        except sqlite3.Error as exc:
            status["error"] = str(exc)

        return status

    @staticmethod
    def _get_directory_status(directory: Path, *, pattern: str) -> dict[str, Any]:
        files = list(directory.rglob(pattern)) if directory.exists() else []

        total_size = sum(file_path.stat().st_size for file_path in files)

        recent_files = sorted(
            files,
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:5]

        return {
            "path": str(directory),
            "exists": directory.exists(),
            "file_count": len(files),
            "total_size_bytes": total_size,
            "recent": [
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                }
                for file_path in recent_files
            ],
        }
