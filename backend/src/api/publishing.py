from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.publishing_channel_service import (
    create_channel,
    get_channel,
    list_channels,
    test_channel,
    update_channel,
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
