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
    "backend/src/api/content_generation.py",
    """
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.repositories.content_asset_repository import (
    ContentAssetRepository,
    ContentAssetRepositoryError,
)
from src.services.content_asset_service import (
    ContentAssetService,
    InvalidContentAssetRequestError,
)
from src.services.content_service import (
    ContentService,
    InvalidContentRequestError,
)


router = APIRouter(prefix="/content", tags=["content"])


class ContentTypeResponse(BaseModel):
    key: str
    label: str
    description: str
    default_tone: str
    default_instructions: str


class ContentTypesResponse(BaseModel):
    content_types: list[ContentTypeResponse]


class ContentAssetResponse(BaseModel):
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


class ContentGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    provider: str | None = None
    language: str | None = None
    tone: str | None = None
    audience: str | None = None
    instructions: str | None = None
    timeout: int | None = None

    project_id: str | None = None
    save_output: bool = False
    asset_title: str | None = None
    asset_status: str | None = None
    asset_metadata: dict[str, Any] | None = None


class ContentGenerateResponse(BaseModel):
    provider: str
    model: str
    topic: str
    content_type: str
    language: str | None
    tone: str | None
    audience: str | None
    instructions: str | None
    prompt: str
    response: str
    saved_content_asset: ContentAssetResponse | None = None


@router.get("/types", response_model=ContentTypesResponse)
def list_content_types() -> dict[str, Any]:
    return {
        "content_types": ContentService.list_content_types(),
    }


@router.get("/types/{key}", response_model=ContentTypeResponse)
def get_content_type(key: str) -> dict[str, Any]:
    try:
        return ContentService.get_content_type(key)
    except InvalidContentRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate", response_model=ContentGenerateResponse)
def generate_content(request: ContentGenerateRequest) -> dict[str, Any]:
    if request.save_output and not request.project_id:
        raise HTTPException(
            status_code=400,
            detail="project_id is required when save_output is true.",
        )

    try:
        generation_result = ContentService.generate_content(
            model=request.model,
            topic=request.topic,
            content_type=request.content_type,
            provider=request.provider,
            language=request.language,
            tone=request.tone,
            audience=request.audience,
            instructions=request.instructions,
            timeout=request.timeout,
        )
    except InvalidContentRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    generation_data = _to_dict(generation_result)
    response_text = str(generation_data.get("response", "")).strip()
    prompt_text = str(generation_data.get("prompt", "")).strip()

    response_payload: dict[str, Any] = {
        "provider": str(generation_data.get("provider") or request.provider or "ollama"),
        "model": str(generation_data.get("model") or request.model),
        "topic": str(generation_data.get("topic") or request.topic),
        "content_type": str(generation_data.get("content_type") or request.content_type),
        "language": generation_data.get("language") or request.language,
        "tone": generation_data.get("tone") or request.tone,
        "audience": generation_data.get("audience") or request.audience,
        "instructions": generation_data.get("instructions") or request.instructions,
        "prompt": prompt_text,
        "response": response_text,
        "saved_content_asset": None,
    }

    if request.save_output:
        try:
            asset = ContentAssetService.build_content_asset(
                project_id=request.project_id or "",
                content_type=response_payload["content_type"],
                title=request.asset_title or _build_asset_title(
                    content_type=response_payload["content_type"],
                    topic=response_payload["topic"],
                ),
                body=response_payload["response"],
                status=request.asset_status,
                source="ai_generated",
                metadata=_build_asset_metadata(
                    request=request,
                    generation_data=generation_data,
                    extra_metadata=request.asset_metadata or {},
                ),
            )
        except InvalidContentAssetRequestError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        repository = ContentAssetRepository()

        try:
            response_payload["saved_content_asset"] = repository.create_content_asset(asset)
        except ContentAssetRepositoryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return response_payload


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    raise HTTPException(
        status_code=500,
        detail="Unsupported content generation result format.",
    )


def _build_asset_title(*, content_type: str, topic: str) -> str:
    clean_content_type = content_type.replace("_", " ").strip().title()
    clean_topic = topic.strip()

    return f"{clean_content_type}: {clean_topic}"


def _build_asset_metadata(
    *,
    request: ContentGenerateRequest,
    generation_data: dict[str, Any],
    extra_metadata: dict[str, Any],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "generator": "content_generate_endpoint",
        "provider": generation_data.get("provider") or request.provider or "ollama",
        "model": generation_data.get("model") or request.model,
        "topic": generation_data.get("topic") or request.topic,
        "content_type": generation_data.get("content_type") or request.content_type,
        "language": generation_data.get("language") or request.language,
        "tone": generation_data.get("tone") or request.tone,
        "audience": generation_data.get("audience") or request.audience,
        "instructions": generation_data.get("instructions") or request.instructions,
        "prompt": generation_data.get("prompt"),
    }

    metadata.update(extra_metadata)

    return metadata
    """,
)


write_file(
    "backend/tests/smoke_test_generation_storage.py",
    """
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app
from src.services.ollama_service import OllamaService


def main() -> None:
    print("DAMA generation storage smoke test started.")

    client = TestClient(app)

    models = OllamaService.list_models()
    assert models
    model_name = models[0].name

    project_name = f"DAMA Generation Storage Project {uuid4().hex[:8]}"

    print("Creating test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Project for generation storage smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]
    print("Test project created.")

    print("Checking POST /content/generate with save_output=true...")
    generation_response = client.post(
        "/content/generate",
        json={
            "model": model_name,
            "topic": "DAMA generation storage smoke test",
            "content_type": "social_caption",
            "instructions": "Reply with exactly this text: DAMA_GENERATION_STORAGE_OK",
            "project_id": project_id,
            "save_output": True,
            "asset_title": "Stored AI Generation Smoke Test",
            "asset_metadata": {
                "smoke_test": True,
            },
            "timeout": 120,
        },
    )
    assert generation_response.status_code == 200, generation_response.text

    generation = generation_response.json()
    assert "DAMA_GENERATION_STORAGE_OK" in generation["response"]
    assert generation["saved_content_asset"] is not None

    saved_asset = generation["saved_content_asset"]
    asset_id = saved_asset["id"]

    assert saved_asset["project_id"] == project_id
    assert saved_asset["source"] == "ai_generated"
    assert saved_asset["title"] == "Stored AI Generation Smoke Test"
    assert "DAMA_GENERATION_STORAGE_OK" in saved_asset["body"]
    assert saved_asset["metadata"]["smoke_test"] is True
    print("POST /content/generate with save_output=true OK.")

    print("Checking saved asset can be loaded...")
    asset_response = client.get(f"/content-assets/{asset_id}")
    assert asset_response.status_code == 200, asset_response.text
    loaded_asset = asset_response.json()
    assert loaded_asset["id"] == asset_id
    assert loaded_asset["project_id"] == project_id
    print("Saved asset load OK.")

    print("Checking save_output=true without project_id...")
    invalid_response = client.post(
        "/content/generate",
        json={
            "model": model_name,
            "topic": "Invalid generation storage request",
            "content_type": "social_caption",
            "save_output": True,
            "timeout": 120,
        },
    )
    assert invalid_response.status_code == 400
    print("Missing project_id check OK.")

    print("DAMA generation storage smoke test passed.")


if __name__ == "__main__":
    main()
    """,
)


write_file(
    "scripts/backend-check.ps1",
    """
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PythonPath = ".\\backend\\.venv\\Scripts\\python.exe"
$AISmokeTestPath = ".\\backend\\tests\\smoke_test_ai.py"
$ProjectSmokeTestPath = ".\\backend\\tests\\smoke_test_projects.py"
$ContentAssetSmokeTestPath = ".\\backend\\tests\\smoke_test_content_assets.py"
$GenerationStorageSmokeTestPath = ".\\backend\\tests\\smoke_test_generation_storage.py"

if (-not (Test-Path $PythonPath)) {
    throw "Python virtual environment was not found at $PythonPath"
}

if (-not (Test-Path $AISmokeTestPath)) {
    throw "AI smoke test was not found at $AISmokeTestPath"
}

if (-not (Test-Path $ProjectSmokeTestPath)) {
    throw "Project smoke test was not found at $ProjectSmokeTestPath"
}

if (-not (Test-Path $ContentAssetSmokeTestPath)) {
    throw "Content asset smoke test was not found at $ContentAssetSmokeTestPath"
}

if (-not (Test-Path $GenerationStorageSmokeTestPath)) {
    throw "Generation storage smoke test was not found at $GenerationStorageSmokeTestPath"
}

Write-Host "Running DAMA backend AI smoke test..."
& $PythonPath $AISmokeTestPath

Write-Host ""
Write-Host "Running DAMA project persistence smoke test..."
& $PythonPath $ProjectSmokeTestPath

Write-Host ""
Write-Host "Running DAMA content asset smoke test..."
& $PythonPath $ContentAssetSmokeTestPath

Write-Host ""
Write-Host "Running DAMA generation storage smoke test..."
& $PythonPath $GenerationStorageSmokeTestPath

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
Write-Host "Backend check completed."
    """,
)


write_file(
    "backend/src/api/index.py",
    """
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
                "description": "Structured content generation, content type catalog, and optional output storage.",
                "endpoints": [
                    "GET /content/types",
                    "GET /content/types/{key}",
                    "POST /content/generate",
                ],
            },
            "content_assets": {
                "description": "Persisted content assets connected to projects.",
                "endpoints": [
                    "POST /content-assets",
                    "GET /content-assets",
                    "GET /content-assets/{asset_id}",
                    "PATCH /content-assets/{asset_id}/status",
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
    """,
)


append_once(
    "docs/backend-api.md",
    "## Generation Storage",
    """
## Generation Storage

POST /content/generate can optionally save generated output as a project-linked content asset.

Additional request fields:

project_id

Required when save_output is true.

save_output

Boolean. When true, generated content is stored as a content asset.

asset_title

Optional title for the saved content asset.

asset_status

Optional status for the saved content asset.

asset_metadata

Optional metadata dictionary for the saved content asset.

Example behavior:

- Generate structured content through the selected provider
- Return the generated response
- Store the generated response as a content asset when save_output is true
- Attach generation metadata to the stored content asset

Current source value for saved generations:

ai_generated
    """,
)


append_once(
    "docs/project-status.md",
    "## Macro Pack 4 Completed",
    """
## Macro Pack 4 Completed

Name:

Generation Storage

Updated files:

- backend/src/api/content_generation.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added files:

- backend/tests/smoke_test_generation_storage.py

Updated behavior:

POST /content/generate can now save generated output as a project-linked content asset.

New request fields:

- project_id
- save_output
- asset_title
- asset_status
- asset_metadata

Purpose:

Connect content generation to persistent project assets.

Next recommended step:

Macro Pack 5: Project Content Workflow

Suggested scope:

- project detail endpoint with attached content assets
- project summary endpoint
- project status updates
- content counts per project
- workflow-ready project state
    """,
)

print("Macro Pack 4 applied successfully.")
