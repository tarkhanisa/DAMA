from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


write_file(
    "backend/tests/smoke_test_generation_storage.py",
    r'''
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app
from src.services.ollama_service import OllamaService


def _first_model_name() -> str:
    models = OllamaService().list_models()

    if not models:
        raise AssertionError("No Ollama models found.")

    first_model = models[0]

    if isinstance(first_model, dict):
        model_name = first_model.get("name") or first_model.get("model")
    else:
        model_name = getattr(first_model, "name", None) or getattr(first_model, "model", None)

    if not model_name:
        raise AssertionError(f"Could not resolve model name from: {first_model!r}")

    return str(model_name)


def main() -> None:
    print("DAMA generation storage smoke test started.")

    client = TestClient(app)

    model_name = _first_model_name()
    print(f"Using model: {model_name}")

    project_name = f"DAMA Generation Storage {uuid4().hex[:8]}"

    print("Creating generation storage project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Generation storage smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Checking POST /content/generate with save_output=true...")
    generation_response = client.post(
        "/content/generate",
        json={
            "model": model_name,
            "topic": "DAMA generation storage smoke test",
            "content_type": "blog_post",
            "instructions": "Return one short sentence about DAMA generation storage.",
            "project_id": project_id,
            "save_output": True,
            "asset_title": "Generation Storage Test Asset",
            "asset_status": "draft",
            "asset_metadata": {
                "smoke_test": "generation_storage",
            },
        },
    )

    assert generation_response.status_code == 200, generation_response.text
    generation_data = generation_response.json()

    assert generation_data["response"]
    assert generation_data["saved_content_asset"] is not None

    saved_asset = generation_data["saved_content_asset"]
    assert saved_asset["project_id"] == project_id
    assert saved_asset["title"] == "Generation Storage Test Asset"
    assert saved_asset["status"] == "draft"
    assert saved_asset["source"] == "ai_generated"
    print("Generation storage OK.")

    print("Checking stored asset through project content assets endpoint...")
    assets_response = client.get(f"/projects/{project_id}/content-assets")
    assert assets_response.status_code == 200, assets_response.text
    assets_data = assets_response.json()
    asset_ids = {asset["id"] for asset in assets_data["content_assets"]}
    assert saved_asset["id"] in asset_ids
    print("Stored asset lookup OK.")

    print("Checking save_output validation without project_id...")
    invalid_response = client.post(
        "/content/generate",
        json={
            "model": model_name,
            "topic": "DAMA invalid storage smoke test",
            "content_type": "blog_post",
            "instructions": "Return one short sentence.",
            "save_output": True,
        },
    )
    assert invalid_response.status_code == 400
    print("save_output validation OK.")

    print("DAMA generation storage smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)

print("Generation storage smoke test hotfix applied.")
