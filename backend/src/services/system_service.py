from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import settings
from src.services.ai_service import AIService
from src.services.content_service import ContentService
from src.services.ollama_service import OllamaService, OllamaServiceError


@dataclass(frozen=True, slots=True)
class SystemStatus:
    """Aggregated DAMA backend system status."""

    app_name: str
    status: str
    ollama_installed: bool
    ollama_version: str | None
    local_models_count: int
    providers_count: int
    content_types_count: int
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "status": self.status,
            "ollama": {
                "installed": self.ollama_installed,
                "version": self.ollama_version,
                "local_models_count": self.local_models_count,
            },
            "providers_count": self.providers_count,
            "content_types_count": self.content_types_count,
            "errors": self.errors,
        }


class SystemService:
    """Service layer for collecting DAMA backend runtime status."""

    @classmethod
    def get_status(cls) -> dict[str, Any]:
        """
        Return aggregated runtime status for the DAMA backend.

        This method uses real service checks and does not return fake values.
        """
        errors: list[str] = []

        ollama_installed = OllamaService.is_installed()
        ollama_version: str | None = None
        local_models_count = 0

        if ollama_installed:
            try:
                ollama_version = OllamaService.version()
            except OllamaServiceError as exc:
                errors.append(f"Ollama version check failed: {exc}")

            try:
                local_models_count = len(OllamaService.list_models())
            except OllamaServiceError as exc:
                errors.append(f"Ollama model listing failed: {exc}")
        else:
            errors.append("Ollama is not installed or is not available in PATH.")

        providers_count = len(AIService.list_providers())
        content_types_count = len(ContentService.list_content_types())

        status = "healthy" if not errors else "degraded"

        system_status = SystemStatus(
            app_name=settings.APP_NAME,
            status=status,
            ollama_installed=ollama_installed,
            ollama_version=ollama_version,
            local_models_count=local_models_count,
            providers_count=providers_count,
            content_types_count=content_types_count,
            errors=errors,
        )

        return system_status.to_dict()
