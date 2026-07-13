from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import shutil


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
BACKUP_ROOT = BACKEND_ROOT / "backups" / "runtime-cleanup"

TARGET_FILES = {
    "channels": DATA_DIR / "publishing_channels.json",
    "variants": DATA_DIR / "publishing_variants.json",
    "attempts": DATA_DIR / "publishing_attempts.json",
    "queue": DATA_DIR / "publishing_queue.json",
}

PRESERVED_CHANNEL_NAMES = {
    "وردپرس لوکال دامامدیا",
    "تلگرام تست دامامدیا",
}

TEST_MARKERS = [
    "smoke",
    "smoke-test",
    "queue smoke",
    "damamedia_queue_test",
    "telegram-real-test",
    "dama queue telegram smoke",
    "dama telegram real test",
    "local test script",
    "first real telegram test",
    "publishing queue dry-run smoke",
    "تست صف انتشار",
    "تست ارسال واقعی",
    "تست تلگرام dama",
]

CHANNEL_TEST_MARKERS = [
    "smoke",
    "queue smoke",
    "damamedia_queue_test",
    "dama queue telegram smoke",
    "dama telegram real test",
    "telegram real test",
]


def utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def write_json_list(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def item_text(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True).lower()


def has_any_marker(item: dict[str, Any], markers: list[str]) -> bool:
    text = item_text(item)
    return any(marker.lower() in text for marker in markers)


def backup_data_dir() -> str:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup_dir = BACKUP_ROOT / utc_slug()
    backup_dir.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            target = backup_dir / item.name

            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    return str(backup_dir)


def split_channels(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    removed_ids: set[str] = set()

    for item in items:
        name = str(item.get("name") or "").strip()

        if name in PRESERVED_CHANNEL_NAMES:
            kept.append(item)
            continue

        if has_any_marker(item, CHANNEL_TEST_MARKERS):
            removed.append(item)
            item_id = str(item.get("id") or "").strip()
            if item_id:
                removed_ids.add(item_id)
            continue

        kept.append(item)

    return kept, removed, removed_ids


def split_variants(
    items: list[dict[str, Any]],
    removed_channel_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    removed_ids: set[str] = set()

    for item in items:
        item_id = str(item.get("id") or "").strip()
        channel_id = str(item.get("channel_id") or "").strip()

        should_remove = channel_id in removed_channel_ids or has_any_marker(item, TEST_MARKERS)

        if should_remove:
            removed.append(item)
            if item_id:
                removed_ids.add(item_id)
            continue

        kept.append(item)

    return kept, removed, removed_ids


def split_attempts(
    items: list[dict[str, Any]],
    removed_variant_ids: set[str],
    removed_channel_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for item in items:
        variant_id = str(item.get("variant_id") or "").strip()
        channel_id = str(item.get("channel_id") or "").strip()

        request = item.get("request")
        if isinstance(request, dict):
            variant_id = variant_id or str(request.get("variant_id") or "").strip()
            channel_id = channel_id or str(request.get("channel_id") or "").strip()

        should_remove = (
            variant_id in removed_variant_ids
            or channel_id in removed_channel_ids
            or has_any_marker(item, TEST_MARKERS)
        )

        if should_remove:
            removed.append(item)
            continue

        kept.append(item)

    return kept, removed


def split_queue(
    items: list[dict[str, Any]],
    removed_variant_ids: set[str],
    removed_channel_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for item in items:
        variant_id = str(item.get("variant_id") or "").strip()
        channel_id = str(item.get("channel_id") or "").strip()

        should_remove = (
            variant_id in removed_variant_ids
            or channel_id in removed_channel_ids
            or has_any_marker(item, TEST_MARKERS)
        )

        if should_remove:
            removed.append(item)
            continue

        kept.append(item)

    return kept, removed


def summarize_file(
    before_items: list[dict[str, Any]],
    after_items: list[dict[str, Any]],
    removed_items: list[dict[str, Any]],
) -> dict[str, Any]:
    removed_ids = [
        str(item.get("id") or "").strip()
        for item in removed_items
        if str(item.get("id") or "").strip()
    ]

    return {
        "before": len(before_items),
        "after": len(after_items),
        "removed": len(removed_items),
        "removed_ids": removed_ids[:50],
    }


def cleanup_test_runtime_data(
    dry_run: bool = True,
    backup: bool = True,
) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    channels = read_json_list(TARGET_FILES["channels"])
    variants = read_json_list(TARGET_FILES["variants"])
    attempts = read_json_list(TARGET_FILES["attempts"])
    queue = read_json_list(TARGET_FILES["queue"])

    kept_channels, removed_channels, removed_channel_ids = split_channels(channels)
    kept_variants, removed_variants, removed_variant_ids = split_variants(
        variants,
        removed_channel_ids,
    )
    kept_attempts, removed_attempts = split_attempts(
        attempts,
        removed_variant_ids,
        removed_channel_ids,
    )
    kept_queue, removed_queue = split_queue(
        queue,
        removed_variant_ids,
        removed_channel_ids,
    )

    summary = {
        "ok": True,
        "dry_run": dry_run,
        "backup_path": "",
        "files": {
            "publishing_channels.json": summarize_file(channels, kept_channels, removed_channels),
            "publishing_variants.json": summarize_file(variants, kept_variants, removed_variants),
            "publishing_attempts.json": summarize_file(attempts, kept_attempts, removed_attempts),
            "publishing_queue.json": summarize_file(queue, kept_queue, removed_queue),
        },
        "totals": {
            "removed": (
                len(removed_channels)
                + len(removed_variants)
                + len(removed_attempts)
                + len(removed_queue)
            )
        },
    }

    if dry_run:
        return summary

    if backup:
        summary["backup_path"] = backup_data_dir()

    write_json_list(TARGET_FILES["channels"], kept_channels)
    write_json_list(TARGET_FILES["variants"], kept_variants)
    write_json_list(TARGET_FILES["attempts"], kept_attempts)
    write_json_list(TARGET_FILES["queue"], kept_queue)

    return summary
