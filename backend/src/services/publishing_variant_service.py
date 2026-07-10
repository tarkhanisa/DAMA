from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json
import re

from src.services.publishing_channel_service import get_channel


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
VARIANTS_PATH = DATA_DIR / "publishing_variants.json"


ALLOWED_VARIANT_STATUSES = {
    "draft",
    "ready_for_review",
    "approved",
    "ready_for_publish",
    "rejected",
    "scheduled",
    "published",
    "failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not VARIANTS_PATH.exists():
        VARIANTS_PATH.write_text("[]\n", encoding="utf-8")


def read_variants() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(VARIANTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_variants(variants: list[dict[str, Any]]) -> None:
    ensure_store()
    VARIANTS_PATH.write_text(
        json.dumps(variants, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_status(status: str | None) -> str:
    value = (status or "draft").strip().lower()

    if value not in ALLOWED_VARIANT_STATUSES:
        return "draft"

    return value


def clean_text(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def limit_text(text: str, max_chars: int) -> str:
    value = clean_text(text)

    if len(value) <= max_chars:
        return value

    return value[: max_chars - 1].rstrip() + ""


def paragraphize(text: str, max_paragraph_chars: int = 360) -> str:
    value = clean_text(text)
    chunks: list[str] = []

    for paragraph in value.split("\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(paragraph) <= max_paragraph_chars:
            chunks.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        current = ""

        for sentence in sentences:
            candidate = (current + " " + sentence).strip()

            if len(candidate) > max_paragraph_chars and current:
                chunks.append(current)
                current = sentence
            else:
                current = candidate

        if current:
            chunks.append(current)

    return "\n\n".join(chunks)


def make_short_hook(title: str, body: str) -> str:
    title = clean_text(title)

    if title:
        return title

    first_line = clean_text(body).split("\n")[0]
    return limit_text(first_line, 80) if first_line else "محتوای تازه"


def make_variant_body(channel_type: str, title: str, body: str) -> tuple[str, str, list[str]]:
    source_title = make_short_hook(title, body)
    source_body = clean_text(body)

    notes: list[str] = []

    if channel_type == "wordpress":
        variant_title = source_title
        variant_body = f"{source_title}\n\n{paragraphize(source_body, 520)}"
        notes = [
            "مناسب پیشنویس وردپرس",
            "قابل استفاده برای توسعه بعدی SEO title و meta description",
            "در این مرحله انتشار واقعی انجام نمیشود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "telegram":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 300)}",
            3500,
        )
        notes = [
            "پاراگرافها کوتاهتر شدهاند",
            "برای پیامرسان مناسبتر است",
            "لینک و CTA در مرحله بعد اضافه میشود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "instagram":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 240)}\n\n#دامامدیا",
            1800,
        )
        notes = [
            "نسخه کپشن است نه مقاله کامل",
            "هشتگ پایه اضافه شده است",
            "تصویر/کاور در مرحله بعدی باید وصل شود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "linkedin":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 420)}",
            2200,
        )
        notes = [
            "لحن برای پست حرفهای مناسبتر شده است",
            "جزئیات اجرایی و رسمی در مرحله AI enhancement بهتر میشود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "whatsapp":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{source_body}",
            700,
        )
        notes = [
            "نسخه کوتاه برای ارسال محدود یا پیام مستقیم",
            "برای ارسال انبوه باید قوانین WhatsApp Business بررسی شود",
        ]
        return variant_title, variant_body, notes

    if channel_type in {"bale", "eitaa"}:
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 300)}",
            2500,
        )
        notes = [
            "نسخه پیامرسان داخلی",
            "اتصال واقعی به API در مرحله بعد بررسی میشود",
        ]
        return variant_title, variant_body, notes

    variant_title = source_title
    variant_body = source_body
    notes = [
        "نسخه دستی برای بازبینی",
        "بدون انتشار خودکار",
    ]

    return variant_title, variant_body, notes


def list_variants(
    content_asset_id: str | None = None,
    channel_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    variants = read_variants()

    if content_asset_id:
        variants = [
            variant
            for variant in variants
            if variant.get("content_asset_id") == content_asset_id
        ]

    if channel_id:
        variants = [
            variant
            for variant in variants
            if variant.get("channel_id") == channel_id
        ]

    if status:
        variants = [
            variant
            for variant in variants
            if variant.get("status") == status
        ]

    return {
        "total": len(variants),
        "items": variants,
    }


def get_variant(variant_id: str) -> dict[str, Any] | None:
    for variant in read_variants():
        if variant.get("id") == variant_id:
            return variant

    return None


def create_variants_plan(payload: dict[str, Any]) -> dict[str, Any]:
    content_asset_id = str(payload.get("content_asset_id") or "").strip()
    source_title = clean_text(str(payload.get("source_title") or payload.get("title") or ""))
    source_body = clean_text(str(payload.get("source_body") or payload.get("body") or ""))
    channel_ids = payload.get("channel_ids")

    if not isinstance(channel_ids, list):
        channel_ids = []

    if not source_body:
        source_body = "متن منبع وارد نشده است. این نسخه فقط برای تست ساختار variant ساخته شده است."

    variants = read_variants()
    created: list[dict[str, Any]] = []
    now = utc_now()

    for raw_channel_id in channel_ids:
        channel_id = str(raw_channel_id or "").strip()
        channel = get_channel(channel_id)

        if not channel:
            continue

        channel_type = str(channel.get("channel_type") or "manual")
        variant_title, variant_body, notes = make_variant_body(
            channel_type=channel_type,
            title=source_title,
            body=source_body,
        )

        variant = {
            "id": str(uuid4()),
            "content_asset_id": content_asset_id,
            "channel_id": channel_id,
            "channel_name": channel.get("name", ""),
            "channel_type": channel_type,
            "source_title": source_title,
            "source_body": source_body,
            "variant_title": variant_title,
            "variant_body": variant_body,
            "status": "draft",
            "adaptation_mode": "rule_based",
            "adaptation_notes": notes,
            "created_at": now,
            "updated_at": now,
        }

        variants.insert(0, variant)
        created.append(variant)

    write_variants(variants)

    return {
        "created": len(created),
        "items": created,
    }


def update_variant_status(variant_id: str, status: str) -> dict[str, Any] | None:
    variants = read_variants()
    normalized_status = normalize_status(status)

    for index, variant in enumerate(variants):
        if variant.get("id") != variant_id:
            continue

        updated = dict(variant)
        updated["status"] = normalized_status
        updated["updated_at"] = utc_now()
        variants[index] = updated
        write_variants(variants)
        return updated

    return None



def review_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    variants = read_variants()
    status = normalize_status(str(payload.get("status") or "ready_for_review"))

    for index, variant in enumerate(variants):
        if variant.get("id") != variant_id:
            continue

        updated = dict(variant)

        if "variant_title" in payload:
            updated["variant_title"] = clean_text(str(payload.get("variant_title") or ""))

        if "variant_body" in payload:
            updated["variant_body"] = clean_text(str(payload.get("variant_body") or ""))

        updated["status"] = status
        updated["review_notes"] = clean_text(str(payload.get("review_notes") or ""))
        updated["reviewed_by"] = clean_text(str(payload.get("reviewed_by") or "operator"))
        updated["reviewed_at"] = utc_now()
        updated["updated_at"] = utc_now()

        history = updated.get("review_history")
        if not isinstance(history, list):
            history = []

        history.append(
            {
                "status": status,
                "review_notes": updated["review_notes"],
                "reviewed_by": updated["reviewed_by"],
                "reviewed_at": updated["reviewed_at"],
            }
        )

        updated["review_history"] = history

        variants[index] = updated
        write_variants(variants)

        return updated

    return None
