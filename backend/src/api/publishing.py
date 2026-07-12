from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.services.publishing_channel_service import (
    create_channel,
    get_channel,
    list_channels,
    test_channel,
    update_channel,
)
from src.services.publishing_variant_ai_service import enhance_variant
from src.services.publishing_variant_service import (
    create_variants_plan,
    get_variant,
    list_variants,
    review_variant,
    update_variant_status,
)
from src.services.wordpress_draft_connector_service import (
    create_wordpress_draft_from_variant,
    get_publish_attempt,
    list_publish_attempts,
)


from src.services.wordpress_draft_connector_service import (
    create_wordpress_draft_from_variant,
    get_publish_attempt,
    list_publish_attempts,
    test_wordpress_connection,
    validate_wordpress_draft_variant,
    wordpress_config_status,
)


from src.services.telegram_connector_service import (
    preview_telegram_variant,
    send_telegram_test_from_variant,
    telegram_config_status,
    test_telegram_connection,
)

from src.services.publishing_queue_service import (
    cancel_queue_item,
    create_queue_item,
    get_queue_item,
    list_queue,
    run_queue_item,
)

router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.get("/channels")
def api_list_channels() -> dict[str, Any]:
    return list_channels()


@router.post("/channels")
def api_create_channel(payload: dict[str, Any]) -> dict[str, Any]:
    return create_channel(payload)


@router.get("/channels/{channel_id}")
def api_get_channel(channel_id: str) -> dict[str, Any]:
    channel = get_channel(channel_id)

    if not channel:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return channel


@router.patch("/channels/{channel_id}")
def api_update_channel(channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    channel = update_channel(channel_id, payload)

    if not channel:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return channel


@router.post("/channels/{channel_id}/test")
def api_test_channel(channel_id: str) -> dict[str, Any]:
    result = test_channel(channel_id)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return result


@router.get("/variants")
def api_list_variants(
    content_asset_id: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_variants(
        content_asset_id=content_asset_id,
        channel_id=channel_id,
        status=status,
    )


@router.post("/variants/plan")
def api_create_variants_plan(payload: dict[str, Any]) -> dict[str, Any]:
    return create_variants_plan(payload)


@router.get("/variants/{variant_id}")
def api_get_variant(variant_id: str) -> dict[str, Any]:
    variant = get_variant(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


@router.patch("/variants/{variant_id}/status")
def api_update_variant_status(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    variant = update_variant_status(variant_id, str(payload.get("status") or "draft"))

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


@router.post("/variants/{variant_id}/enhance")
def api_enhance_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = enhance_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.patch("/variants/{variant_id}/review")
def api_review_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    variant = review_variant(variant_id, payload)

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


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



@router.get("/telegram/config")
def api_telegram_config() -> dict[str, Any]:
    return telegram_config_status()


@router.post("/telegram/test")
def api_telegram_test(payload: dict[str, Any]) -> dict[str, Any]:
    return test_telegram_connection(payload)


@router.post("/variants/{variant_id}/telegram/preview")
def api_preview_telegram_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = preview_telegram_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result


@router.post("/variants/{variant_id}/telegram/send-test")
def api_send_telegram_test(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = send_telegram_test_from_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result



@router.get("/queue")
def api_list_publishing_queue(
    status: str | None = Query(default=None),
    connector: str | None = Query(default=None),
    variant_id: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_queue(
        status=status,
        connector=connector,
        variant_id=variant_id,
    )


@router.post("/queue")
def api_create_publishing_queue_item(payload: dict[str, Any]) -> dict[str, Any]:
    result = create_queue_item(payload)

    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "Queue item could not be created.")

    return result


@router.get("/queue/{queue_id}")
def api_get_publishing_queue_item(queue_id: str) -> dict[str, Any]:
    item = get_queue_item(queue_id)

    if not item:
        raise HTTPException(status_code=404, detail="Publishing queue item not found.")

    return item


@router.post("/queue/{queue_id}/run")
def api_run_publishing_queue_item(queue_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = run_queue_item(queue_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing queue item not found.")

    return result


@router.post("/queue/{queue_id}/cancel")
def api_cancel_publishing_queue_item(queue_id: str) -> dict[str, Any]:
    result = cancel_queue_item(queue_id)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing queue item not found.")

    return result
