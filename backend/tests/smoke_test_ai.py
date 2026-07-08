from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.main import app
from src.services.ai_service import AIService
from src.services.content_service import ContentService
from src.services.ollama_service import OllamaService
from src.services.prompt_service import PromptService
from src.services.system_service import SystemService


TEST_MODEL = "qwen2.5-coder:7b"


def main() -> None:
    print("DAMA backend fast smoke test started.")

    print("Checking Ollama installation...")
    assert OllamaService.is_installed() is True

    print("Checking Ollama version...")
    version = OllamaService.version()
    assert version
    print(f"Ollama version: {version}")

    print("Checking local models...")
    models = OllamaService.list_models()
    assert isinstance(models, list)
    assert any(model["name"] == TEST_MODEL for model in models)
    print(f"Found model: {TEST_MODEL}")

    print("Checking PromptService rendering...")
    rendered_prompt = PromptService.render_to_string(
        template="Reply with exactly this text: {text}",
        variables={"text": "DAMA_SMOKE_PROMPT_SERVICE_OK"},
    )
    assert rendered_prompt == "Reply with exactly this text: DAMA_SMOKE_PROMPT_SERVICE_OK"
    print("PromptService rendering OK.")

    print("Checking AI provider catalog...")
    providers = AIService.list_providers()
    provider_keys = {provider["key"] for provider in providers}
    assert "ollama" in provider_keys
    assert AIService.get_provider("ollama")["supports_text_generation"] is True
    print("AI provider catalog OK.")

    print("Checking content type catalog...")
    content_types = ContentService.list_content_types()
    content_type_keys = {content_type["key"] for content_type in content_types}
    assert "blog_post" in content_type_keys
    assert "social_caption" in content_type_keys
    assert "product_description" in content_type_keys
    assert "video_script" in content_type_keys
    assert "email_campaign" in content_type_keys
    assert "press_release" in content_type_keys
    assert ContentService.get_content_type("product_description")["default_tone"] == "persuasive"
    print("Content type catalog OK.")

    print("Checking system status service...")
    system_status = SystemService.get_status()
    assert system_status["status"] in {"healthy", "degraded"}
    assert system_status["ollama"]["installed"] is True
    assert system_status["ollama"]["local_models_count"] >= 1
    assert system_status["providers_count"] >= 1
    assert system_status["content_types_count"] >= 6
    print("System status service OK.")

    client = TestClient(app)

    print("Checking GET /api...")
    api_index_response = client.get("/api")
    assert api_index_response.status_code == 200
    api_index_json = api_index_response.json()
    capability_keys = {
        capability["key"]
        for capability in api_index_json["capabilities"]
    }
    assert "models" in capability_keys
    assert "generation" in capability_keys
    assert "content" in capability_keys
    assert "providers" in capability_keys
    assert "system" in capability_keys
    print("GET /api OK.")

    print("Checking GET /models...")
    models_response = client.get("/models")
    assert models_response.status_code == 200
    assert "models" in models_response.json()
    print("GET /models OK.")

    print("Checking GET /providers...")
    providers_response = client.get("/providers")
    assert providers_response.status_code == 200
    assert "providers" in providers_response.json()
    print("GET /providers OK.")

    print("Checking GET /providers/ollama...")
    ollama_provider_response = client.get("/providers/ollama")
    assert ollama_provider_response.status_code == 200
    assert ollama_provider_response.json()["key"] == "ollama"
    print("GET /providers/ollama OK.")

    print("Checking invalid GET /providers/fake...")
    invalid_provider_response = client.get("/providers/fake")
    assert invalid_provider_response.status_code == 400
    print("Invalid provider endpoint OK.")

    print("Checking GET /content/types...")
    content_types_response = client.get("/content/types")
    assert content_types_response.status_code == 200
    assert "content_types" in content_types_response.json()
    print("GET /content/types OK.")

    print("Checking GET /content/types/social_caption...")
    single_content_type_response = client.get("/content/types/social_caption")
    assert single_content_type_response.status_code == 200
    assert single_content_type_response.json()["key"] == "social_caption"
    print("GET /content/types/social_caption OK.")

    print("Checking invalid GET /content/types/fake_type...")
    invalid_content_type_response = client.get("/content/types/fake_type")
    assert invalid_content_type_response.status_code == 400
    print("Invalid content type endpoint OK.")

    print("Checking GET /system/status...")
    system_status_response = client.get("/system/status")
    assert system_status_response.status_code == 200
    system_status_json = system_status_response.json()
    assert system_status_json["status"] in {"healthy", "degraded"}
    assert system_status_json["ollama"]["installed"] is True
    print("GET /system/status OK.")

    print("Checking invalid POST /content/generate content type...")
    invalid_content_generation_response = client.post(
        "/content/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "topic": "DAMA",
            "content_type": "fake_type",
            "timeout": 120,
        },
    )
    assert invalid_content_generation_response.status_code == 400
    print("Invalid /content/generate content type OK.")

    print("Checking one real AI generation through POST /generate...")
    generate_response = client.post(
        "/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "prompt": "Reply with exactly this text: DAMA_FAST_SMOKE_OK",
            "timeout": 240,
        },
    )
    assert generate_response.status_code == 200
    generate_json = generate_response.json()
    assert generate_json["provider"] == "ollama"
    assert generate_json["model"] == TEST_MODEL
    assert "DAMA_FAST_SMOKE_OK" in generate_json["response"]
    print("POST /generate real generation OK.")

    print("DAMA backend fast smoke test passed.")


if __name__ == "__main__":
    main()
