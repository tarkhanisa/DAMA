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
