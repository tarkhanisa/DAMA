from pathlib import Path

ROOT = Path("I:/DAMA")


def patch_file(path: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")

    if "_extract_generated_text" not in text:
        helper = r'''

def _extract_generated_text(generation_data: dict[str, Any]) -> str:
    possible_keys = [
        "response",
        "content",
        "body",
        "text",
        "output",
        "result",
        "generated_text",
        "generated_content",
    ]

    for key in possible_keys:
        value = generation_data.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    nested_generation = generation_data.get("generation")

    if isinstance(nested_generation, dict):
        for key in possible_keys:
            value = nested_generation.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

    nested_data = generation_data.get("data")

    if isinstance(nested_data, dict):
        for key in possible_keys:
            value = nested_data.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""
'''
        text = text.rstrip() + "\n" + helper + "\n"

    text = text.replace(
        'response_text = str(generation_data.get("response", "")).strip()',
        'response_text = _extract_generated_text(generation_data)',
    )

    text = text.replace(
        "response_text = str(generation_data.get('response', '')).strip()",
        "response_text = _extract_generated_text(generation_data)",
    )

    if path.endswith("content_generation.py") and "AI generation returned empty content." not in text:
        text = text.replace(
            "response_text = _extract_generated_text(generation_data)\n",
            "response_text = _extract_generated_text(generation_data)\n\n    if not response_text:\n        raise HTTPException(status_code=502, detail=\"AI generation returned empty content.\")\n",
            1,
        )

    if path.endswith("workflows.py") and "AI generation returned empty content." not in text:
        text = text.replace(
            "response_text = _extract_generated_text(generation_data)\n",
            "response_text = _extract_generated_text(generation_data)\n\n    if not response_text:\n        raise HTTPException(status_code=502, detail=\"AI generation returned empty content.\")\n",
            1,
        )

    target.write_text(text, encoding="utf-8")
    print(f"Patched {path}")


patch_file("backend/src/api/content_generation.py")
patch_file("backend/src/api/workflows.py")

print("Generated text extraction hotfix applied.")
