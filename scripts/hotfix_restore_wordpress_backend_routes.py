from pathlib import Path

ROOT = Path("I:/DAMA")

api_path = ROOT / "backend/src/api/publishing.py"
api_path.parent.mkdir(parents=True, exist_ok=True)

text = api_path.read_text(encoding="utf-8") if api_path.exists() else ""

required_import = """from src.services.wordpress_draft_connector_service import (
    create_wordpress_draft_from_variant,
    get_publish_attempt,
    list_publish_attempts,
    test_wordpress_connection,
    validate_wordpress_draft_variant,
    wordpress_config_status,
)
"""

if "wordpress_config_status" not in text:
    if "from fastapi import APIRouter" not in text:
        text = """from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

""" + required_import + """

router = APIRouter(prefix="/publishing", tags=["publishing"])
"""
    else:
        text = text.replace(
            "router = APIRouter",
            required_import + "\n\nrouter = APIRouter",
            1,
        )

if '@router.get("/wordpress/config")' not in text:
    text += r'''


@router.get("/wordpress/config")
def api_wordpress_config() -> dict[str, Any]:
    return wordpress_config_status()


@router.post("/wordpress/test")
def api_wordpress_test(payload: dict[str, Any]) -> dict[str, Any]:
    return test_wordpress_connection(payload)


@router.post("/variants/{variant_id}/wordpress/validate")
def api_validate_wordpress_draft(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_wordpress_draft_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.post("/variants/{variant_id}/wordpress/draft")
def api_create_wordpress_draft(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = create_wordpress_draft_from_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.get("/attempts")
def api_list_publish_attempts(
    variant_id: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_publish_attempts(
        variant_id=variant_id,
        channel_id=channel_id,
        status=status,
    )


@router.get("/attempts/{attempt_id}")
def api_get_publish_attempt(attempt_id: str) -> dict[str, Any]:
    attempt = get_publish_attempt(attempt_id)

    if not attempt:
        raise HTTPException(status_code=404, detail="Publishing attempt not found.")

    return attempt
'''

api_path.write_text(text.strip() + "\n", encoding="utf-8")
print("WordPress publishing backend routes restored.")
