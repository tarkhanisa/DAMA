from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.main import app
from src.services.ai_service import AIService
from src.services.ollama_service import OllamaService


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

    print("Checking AIService generation...")
    ai_result = AIService.generate_text(
        model=TEST_MODEL,
        prompt="Reply with exactly this text: DAMA_SMOKE_AI_OK",
        provider="ollama",
        timeout=120,
    )
    assert ai_result["provider"] == "ollama"
    assert ai_result["model"] == TEST_MODEL
    assert "DAMA_SMOKE_AI_OK" in ai_result["response"]
    print("AIService generation OK.")

    client = TestClient(app)

    print("Checking GET /models...")
    models_response = client.get("/models")
    assert models_response.status_code == 200
    assert "models" in models_response.json()
    print("GET /models OK.")

    print("Checking POST /generate...")
    generate_response = client.post(
        "/generate",
        json={
            "provider": "ollama",
            "model": TEST_MODEL,
            "prompt": "Reply with exactly this text: DAMA_SMOKE_API_OK",
            "timeout": 120,
        },
    )
    assert generate_response.status_code == 200
    generate_json = generate_response.json()
    assert generate_json["provider"] == "ollama"
    assert generate_json["model"] == TEST_MODEL
    assert "DAMA_SMOKE_API_OK" in generate_json["response"]
    print("POST /generate OK.")

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
