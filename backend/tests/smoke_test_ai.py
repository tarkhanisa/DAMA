from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.main import app
from src.services.ai_service import AIService
from src.services.content_service import ContentGenerationRequest, ContentService
from src.services.ollama_service import OllamaService
from src.services.prompt_service import PromptService


TEST_MODEL = "qwen2.5-coder:7b"


def main() -> None:
    print("DAMA backend AI smoke test started.")

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

    print("Checking ContentService content types...")
    content_types = ContentService.list_content_types()
    content_type_keys = {content_type["key"] for content_type in content_types}
    assert "blog_post" in content_type_keys
    assert "social_caption" in content_type_keys
    assert "product_description" in content_type_keys
    assert "video_script" in content_type_keys
    assert "email_campaign" in content_type_keys
    assert "press_release" in content_type_keys
    print("ContentService content types OK.")

    print("Checking ContentService prompt building...")
    content_request = ContentGenerationRequest(
        model=TEST_MODEL,
        topic="DAMA AI content automation platform",
        content_type="product_description",
        provider="ollama",
        language="English",
        tone="professional",
        audience="content teams and creators",
        instructions="Write only one short paragraph.",
        timeout=120,
    )
    content_prompt = ContentService.build_prompt(content_request)
    assert "DAMA AI content automation platform" in content_prompt
    assert "product_description" in content_prompt
    assert "professional" in content_prompt
    print("ContentService prompt building OK.")

    print("Checking AIService generation with direct prompt...")
    ai_prompt_result = AIService.generate_text(
        model=TEST_MODEL,
        prompt="Reply with exactly this text: DAMA_SMOKE_AI_PROMPT_OK",
        provider="ollama",
        timeout=120,
    )
    assert ai_prompt_result["provider"] == "ollama"
    assert ai_prompt_result["model"] == TEST_MODEL
    assert "DAMA_SMOKE_AI_PROMPT_OK" in ai_prompt_result["response"]
    print("AIService direct prompt generation OK.")

    print("Checking AIService generation with template...")
    ai_template_result = AIService.generate_text(
        model=TEST_MODEL,
        template="Reply with exactly this text: {text}",
        variables={"text": "DAMA_SMOKE_AI_TEMPLATE_OK"},
        provider="ollama",
        timeout=120,
    )
    assert ai_template_result["provider"] == "ollama"
    assert ai_template_result["model"] == TEST_MODEL
    assert "DAMA_SMOKE_AI_TEMPLATE_OK" in ai_template_result["response"]
    print("AIService template generation OK.")

    client = TestClient(app)

    print("Checking GET /models...")
    models_response = client.get("/models")
    assert models_response.status_code == 200
    assert "models" in models_response.json()
    print("GET /models OK.")

    print("Checking GET /content/types...")
    content_types_response = client.get("/content/types")
    assert content_types_response.status_code == 200
    content_types_json = content_types_response.json()
    assert "content_types" in content_types_json
    api_content_type_keys = {
        content_type["key"]
        for content_type in content_types_json["content_types"]
    }
    assert "blog_post" in api_content_type_keys
    assert "social_caption" in api_content_type_keys
    assert "product_description" in api_content_type_keys
    assert "video_script" in api_content_type_keys
    assert "email_campaign" in api_content_type_keys
    assert "press_release" in api_content_type_keys
    print("GET /content/types OK.")

    print("Checking GET /content/types/social_caption...")
    single_content_type_response = client.get("/content/types/social_caption")
    assert single_content_type_response.status_code == 200
    single_content_type_json = single_content_type_response.json()
    assert single_content_type_json["key"] == "social_caption"
    assert single_content_type_json["label"] == "Social caption"
    print("GET /content/types/social_caption OK.")

    print("Checking invalid GET /content/types/fake_type...")
    invalid_content_type_response = client.get("/content/types/fake_type")
    assert invalid_content_type_response.status_code == 400
    assert "fake_type" in str(invalid_content_type_response.json())
    print("Invalid single content type validation OK.")

    print("Checking POST /generate with direct prompt...")
    generate_prompt_response = client.post(
        "/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "prompt": "Reply with exactly this text: DAMA_SMOKE_API_PROMPT_OK",
            "timeout": 120,
        },
    )
    assert generate_prompt_response.status_code == 200
    generate_prompt_json = generate_prompt_response.json()
    assert generate_prompt_json["provider"] == "ollama"
    assert generate_prompt_json["model"] == TEST_MODEL
    assert "DAMA_SMOKE_API_PROMPT_OK" in generate_prompt_json["response"]
    print("POST /generate direct prompt OK.")

    print("Checking POST /generate with template...")
    generate_template_response = client.post(
        "/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "template": "Reply with exactly this text: {text}",
            "variables": {
                "text": "DAMA_SMOKE_API_TEMPLATE_OK",
            },
            "timeout": 120,
        },
    )
    assert generate_template_response.status_code == 200
    generate_template_json = generate_template_response.json()
    assert generate_template_json["provider"] == "ollama"
    assert generate_template_json["model"] == TEST_MODEL
    assert "DAMA_SMOKE_API_TEMPLATE_OK" in generate_template_json["response"]
    print("POST /generate template OK.")

    print("Checking POST /content/generate...")
    content_response = client.post(
        "/content/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "topic": "DAMA AI content automation platform",
            "content_type": "product_description",
            "language": "English",
            "tone": "professional",
            "audience": "content teams",
            "instructions": "Write only one short sentence.",
            "timeout": 120,
        },
    )
    assert content_response.status_code == 200
    content_json = content_response.json()
    assert content_json["provider"] == "ollama"
    assert content_json["model"] == TEST_MODEL
    assert content_json["content_type"] == "product_description"
    assert content_json["topic"] == "DAMA AI content automation platform"
    assert content_json["content"]
    assert content_json["prompt"]
    print("POST /content/generate OK.")

    print("Checking /content/generate validation...")
    invalid_content_response = client.post(
        "/content/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "content_type": "post",
        },
    )
    assert invalid_content_response.status_code == 422
    print("/content/generate validation OK.")

    print("Checking missing template variable validation...")
    missing_variable_response = client.post(
        "/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "template": "Write about {topic} in {tone} tone.",
            "variables": {
                "topic": "DAMA",
            },
            "timeout": 120,
        },
    )
    assert missing_variable_response.status_code == 400
    assert "tone" in str(missing_variable_response.json())
    print("Missing template variable validation OK.")

    print("Checking unsupported provider validation...")
    invalid_provider_response = client.post(
        "/generate",
        json={
            "provider": "fake",
            "model": TEST_MODEL,
            "prompt": "test",
        },
    )
    assert invalid_provider_response.status_code == 400
    print("Unsupported provider validation OK.")

    print("DAMA backend AI smoke test passed.")


if __name__ == "__main__":
    main()


