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
