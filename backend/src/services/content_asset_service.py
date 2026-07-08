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
