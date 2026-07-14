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

from src.services.runtime_cleanup_service import cleanup_test_runtime_data

from src.services.media_campaign_service import (
    create_media_campaign,
    get_media_campaign,
    list_media_campaigns,
    update_media_campaign,
)

from src.services.local_video_service import (
    create_video_job,
    get_video_job,
    list_video_jobs,
    local_video_config,
    run_video_job,
)

from src.services.local_ai_tools_service import (
    enhance_local_video_prompt,
    local_ai_tools_status,
)

from src.services.operator_session_service import (
    read_operator_session,
    safe_exit,
    update_last_route,
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



@router.get("/cleanup/test-data/preview")
def api_preview_test_data_cleanup() -> dict[str, Any]:
    return cleanup_test_runtime_data(dry_run=True)


@router.post("/cleanup/test-data/run")
def api_run_test_data_cleanup(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = payload or {}
    backup = bool(request.get("backup", True))
    return cleanup_test_runtime_data(dry_run=False, backup=backup)



@router.get("/campaigns")
def api_list_media_campaigns(
    status: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    return list_media_campaigns(status=status, project_id=project_id)


@router.post("/campaigns")
def api_create_media_campaign(payload: dict[str, Any]) -> dict[str, Any]:
    return create_media_campaign(payload)


@router.get("/campaigns/{campaign_id}")
def api_get_media_campaign(campaign_id: str) -> dict[str, Any]:
    campaign = get_media_campaign(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Media campaign not found.")

    return campaign


@router.patch("/campaigns/{campaign_id}")
def api_update_media_campaign(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    campaign = update_media_campaign(campaign_id, payload)

    if not campaign:
        raise HTTPException(status_code=404, detail="Media campaign not found.")

    return campaign



@router.get("/local-video/config")
def api_local_video_config() -> dict[str, Any]:
    return local_video_config()


@router.get("/local-video/jobs")
def api_list_local_video_jobs(status: str | None = None) -> dict[str, Any]:
    return list_video_jobs(status=status)


@router.post("/local-video/jobs")
def api_create_local_video_job(payload: dict[str, Any]) -> dict[str, Any]:
    return create_video_job(payload)


@router.get("/local-video/jobs/{job_id}")
def api_get_local_video_job(job_id: str) -> dict[str, Any]:
    job = get_video_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Local video job not found.")

    return job


@router.post("/local-video/jobs/{job_id}/run")
def api_run_local_video_job(job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    result = run_video_job(job_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Local video job not found.")

    return result



@router.get("/local-tools/status")
def api_local_ai_tools_status() -> dict[str, Any]:
    return local_ai_tools_status()


@router.post("/local-video/prompt/enhance")
def api_enhance_local_video_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    return enhance_local_video_prompt(payload)



@router.get("/operator/session")
def api_get_operator_session() -> dict[str, Any]:
    return read_operator_session()


@router.post("/operator/session/route")
def api_update_operator_route(payload: dict[str, Any]) -> dict[str, Any]:
    return update_last_route(payload.get("last_route"))


@router.post("/operator/session/safe-exit")
def api_operator_safe_exit(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return safe_exit(payload)



@router.get("/local-video/jobs/{job_id}/output")
def api_get_local_video_output(job_id: str):
    from pathlib import Path

    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    from src.services.local_video_service import get_video_job

    job = get_video_job(job_id)

    if not isinstance(job, dict):
        raise HTTPException(status_code=404, detail="Local video job not found.")

    output_path = Path(str(job.get("output_path") or ""))

    if not output_path.is_file():
        raise HTTPException(status_code=404, detail="Local video output file not found.")

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=output_path.name,
    )


@router.post("/local-video/jobs/{job_id}/open-output-folder")
def api_open_local_video_output_folder(job_id: str):
    from pathlib import Path
    import os
    import subprocess
    import sys

    from fastapi import HTTPException

    from src.services.local_video_service import get_video_job

    job = get_video_job(job_id)

    if not isinstance(job, dict):
        raise HTTPException(status_code=404, detail="Local video job not found.")

    output_path = Path(str(job.get("output_path") or ""))

    if not output_path:
        raise HTTPException(status_code=404, detail="Local video output path is empty.")

    folder = output_path.parent

    if not folder.exists():
        raise HTTPException(status_code=404, detail="Local video output folder not found.")

    try:
        if os.name == "nt":
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not open output folder: {exc}") from exc

    return {
        "ok": True,
        "folder": str(folder),
        "message": "Output folder open request sent.",
    }
