from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ExportServiceError(RuntimeError):
    pass


class InvalidExportRequestError(ExportServiceError):
    pass


@dataclass(frozen=True, slots=True)
class ExportResult:
    export_type: str
    file_name: str
    file_path: str
    title: str
    created_at: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "export_type": self.export_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "title": self.title,
            "created_at": self.created_at,
            "content": self.content,
        }


class ExportService:
    @classmethod
    def export_content_asset_markdown(
        cls,
        *,
        content_asset: dict[str, Any],
        export_root: Path | None = None,
    ) -> dict[str, Any]:
        asset_id = cls._required(content_asset.get("id"), "Content asset ID")
        title = cls._required(content_asset.get("title"), "Content asset title")
        body = cls._required(content_asset.get("body"), "Content asset body")
        content_type = cls._required(content_asset.get("content_type"), "Content type")
        status = cls._required(content_asset.get("status"), "Content asset status")
        source = cls._required(content_asset.get("source"), "Content asset source")
        project_id = cls._required(content_asset.get("project_id"), "Project ID")

        created_at = datetime.now(UTC).isoformat()

        markdown = cls._build_content_asset_markdown(
            title=title,
            body=body,
            content_type=content_type,
            status=status,
            source=source,
            project_id=project_id,
            asset_id=asset_id,
            created_at=created_at,
        )

        export_directory = cls._get_export_root(export_root) / "content-assets"
        export_directory.mkdir(parents=True, exist_ok=True)

        file_name = f"{cls._slugify(title)}-{asset_id[:8]}.md"
        file_path = export_directory / file_name

        file_path.write_text(markdown, encoding="utf-8")

        return ExportResult(
            export_type="content_asset_markdown",
            file_name=file_name,
            file_path=str(file_path),
            title=title,
            created_at=created_at,
            content=markdown,
        ).to_dict()

    @classmethod
    def export_project_markdown_bundle(
        cls,
        *,
        project: dict[str, Any],
        content_assets: list[dict[str, Any]],
        export_root: Path | None = None,
    ) -> dict[str, Any]:
        project_id = cls._required(project.get("id"), "Project ID")
        project_name = cls._required(project.get("name"), "Project name")
        project_type = cls._required(project.get("project_type"), "Project type")
        project_status = cls._required(project.get("status"), "Project status")

        created_at = datetime.now(UTC).isoformat()

        markdown = cls._build_project_bundle_markdown(
            project=project,
            content_assets=content_assets,
            created_at=created_at,
        )

        export_directory = cls._get_export_root(export_root) / "projects"
        export_directory.mkdir(parents=True, exist_ok=True)

        file_name = f"{cls._slugify(project_name)}-{project_id[:8]}-bundle.md"
        file_path = export_directory / file_name

        file_path.write_text(markdown, encoding="utf-8")

        return ExportResult(
            export_type="project_markdown_bundle",
            file_name=file_name,
            file_path=str(file_path),
            title=f"{project_name} Bundle",
            created_at=created_at,
            content=markdown,
        ).to_dict()

    @staticmethod
    def _build_content_asset_markdown(
        *,
        title: str,
        body: str,
        content_type: str,
        status: str,
        source: str,
        project_id: str,
        asset_id: str,
        created_at: str,
    ) -> str:
        return (
            f"# {title}\n\n"
            f"Asset ID: {asset_id}\n\n"
            f"Project ID: {project_id}\n\n"
            f"Content Type: {content_type}\n\n"
            f"Status: {status}\n\n"
            f"Source: {source}\n\n"
            f"Exported At: {created_at}\n\n"
            "---\n\n"
            f"{body}\n"
        )

    @classmethod
    def _build_project_bundle_markdown(
        cls,
        *,
        project: dict[str, Any],
        content_assets: list[dict[str, Any]],
        created_at: str,
    ) -> str:
        project_name = cls._required(project.get("name"), "Project name")
        project_id = cls._required(project.get("id"), "Project ID")
        project_type = cls._required(project.get("project_type"), "Project type")
        project_status = cls._required(project.get("status"), "Project status")

        sections = [
            f"# {project_name}",
            "",
            f"Project ID: {project_id}",
            "",
            f"Project Type: {project_type}",
            "",
            f"Project Status: {project_status}",
            "",
            f"Exported At: {created_at}",
            "",
            f"Total Content Assets: {len(content_assets)}",
            "",
            "---",
            "",
        ]

        if not content_assets:
            sections.append("No content assets found for this project.")
            sections.append("")
            return "\n".join(sections)

        for index, asset in enumerate(content_assets, start=1):
            title = cls._required(asset.get("title"), "Content asset title")
            body = cls._required(asset.get("body"), "Content asset body")
            content_type = cls._required(asset.get("content_type"), "Content type")
            status = cls._required(asset.get("status"), "Content asset status")
            source = cls._required(asset.get("source"), "Content asset source")
            asset_id = cls._required(asset.get("id"), "Content asset ID")

            sections.extend(
                [
                    f"## {index}. {title}",
                    "",
                    f"Asset ID: {asset_id}",
                    "",
                    f"Content Type: {content_type}",
                    "",
                    f"Status: {status}",
                    "",
                    f"Source: {source}",
                    "",
                    body,
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(sections)

    @staticmethod
    def _get_export_root(export_root: Path | None = None) -> Path:
        if export_root is not None:
            return export_root

        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / "exports"

    @staticmethod
    def _required(value: Any, field_name: str) -> str:
        normalized_value = str(value or "").strip()

        if not normalized_value:
            raise InvalidExportRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @staticmethod
    def _slugify(value: str) -> str:
        normalized_value = value.strip().lower()
        normalized_value = re.sub(r"[^a-z0-9]+", "-", normalized_value)
        normalized_value = normalized_value.strip("-")

        if not normalized_value:
            return "export"

        return normalized_value
