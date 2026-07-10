from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.services.publishing_variant_service import (
    read_variants,
    write_variants,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def channel_instruction(channel_type: str) -> str:
    instructions = {
        "wordpress": """
نسخه را برای پیشنویس وردپرس بهتر کن.
خروجی باید شامل تیتر مناسب لید کوتاه و متن اصلی منظم باشد.
متن باید برای سایت مناسب باشد نه کپشن شبکه اجتماعی.
از ایموجی استفاده نکن.
اگر متن فارسی است فارسی روان و طبیعی بنویس.
""",
        "telegram": """
نسخه را برای تلگرام بهتر کن.
پاراگرافها کوتاه خوانا و مناسب موبایل باشند.
متن بیش از حد رسمی یا طولانی نباشد.
از ایموجی زیاد استفاده نکن اگر لازم نیست اصلا استفاده نکن.
لینک ساختگی اضافه نکن.
""",
        "instagram": """
نسخه را برای کپشن اینستاگرام بهتر کن.
شروع باید جذاب باشد اما سطحی و کلیشهای نباشد.
متن باید کوتاهتر از مقاله باشد.
هشتگها محدود و مرتبط باشند.
از ایموجی فقط در صورت ضرورت و بسیار کم استفاده کن.
""",
        "linkedin": """
نسخه را برای لینکدین بهتر کن.
لحن حرفهای روشن و قابل ارائه باشد.
متن باید برای مخاطب کسبوکار سرمایهگذار یا همکار حرفهای قابل قبول باشد.
از شعارهای عمومی و اغراق پرهیز کن.
""",
        "whatsapp": """
نسخه را برای واتساپ بهتر کن.
متن باید کوتاه مستقیم انسانی و قابل ارسال باشد.
از متن طولانی هشتگ زیاد و لحن تبلیغاتی سنگین پرهیز کن.
""",
        "bale": """
نسخه را برای پیامرسان بله بهتر کن.
متن باید خوانا ساده و مناسب انتشار در کانال یا گروه باشد.
""",
        "eitaa": """
نسخه را برای پیامرسان ایتا بهتر کن.
متن باید خوانا ساده و مناسب انتشار در کانال یا گروه باشد.
""",
        "manual": """
نسخه را برای بازبینی انسانی تمیز و منظم کن.
هدف خوانایی و آماده بودن برای ویرایش دستی است.
""",
    }

    return instructions.get(channel_type, instructions["manual"]).strip()


def build_prompt(variant: dict[str, Any], extra_instruction: str = "") -> str:
    channel_type = str(variant.get("channel_type") or "manual")
    variant_title = str(variant.get("variant_title") or "").strip()
    variant_body = str(variant.get("variant_body") or "").strip()
    source_title = str(variant.get("source_title") or "").strip()
    source_body = str(variant.get("source_body") or "").strip()

    return f"""
نقش شما:
شما ویراستار و استراتژیست محتوای چندکاناله دامامدیا هستید.

وظیفه:
نسخه زیر را برای کانال مشخصشده بهتر و آمادهتر کن.

کانال:
{channel_type}

دستور اختصاصی کانال:
{channel_instruction(channel_type)}

عنوان منبع:
{source_title}

متن مادر:
{source_body}

عنوان نسخه فعلی:
{variant_title}

متن نسخه فعلی:
{variant_body}

دستور تکمیلی اپراتور:
{extra_instruction or "دستور تکمیلی وجود ندارد."}

قوانین:
- خروجی فقط نسخه نهایی قابل استفاده باشد.
- توضیح نده که چه کار کردی.
- JSON تولید نکن.
- markdown سنگین تولید نکن مگر برای خوانایی تیترها.
- اطلاعات ساختگی آمار جایزه یا همکاری واقعی اضافه نکن.
- متن را مخصوص همین کانال بهتر کن.
- اگر زبان متن فارسی است فارسی طبیعی و غیرترجمهای بنویس.
""".strip()


def dry_run_enhancement(variant: dict[str, Any]) -> str:
    title = str(variant.get("variant_title") or "").strip()
    body = str(variant.get("variant_body") or "").strip()
    channel_type = str(variant.get("channel_type") or "manual")

    prefix = {
        "wordpress": "نسخه پیشنهادی برای وردپرس",
        "telegram": "نسخه پیشنهادی برای تلگرام",
        "instagram": "نسخه پیشنهادی برای اینستاگرام",
        "linkedin": "نسخه پیشنهادی برای لینکدین",
        "whatsapp": "نسخه پیشنهادی برای واتساپ",
        "bale": "نسخه پیشنهادی برای بله",
        "eitaa": "نسخه پیشنهادی برای ایتا",
        "manual": "نسخه پیشنهادی برای بازبینی دستی",
    }.get(channel_type, "نسخه پیشنهادی")

    if title and not body.startswith(title):
        return f"{prefix}\n\n{title}\n\n{body}".strip()

    return f"{prefix}\n\n{body}".strip()


def ollama_generate(prompt: str, model: str | None = None) -> str:
    base_url = os.getenv("DAMA_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    selected_model = model or os.getenv("DAMA_OLLAMA_DEFAULT_MODEL", "qwen2.5-coder:7b")

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
        },
    }

    request = Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw)

    generated = str(data.get("response") or "").strip()

    if not generated:
        raise RuntimeError("Ollama returned an empty response.")

    return generated


def enhance_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    variants = read_variants()
    mode = str(payload.get("mode") or "dry_run").strip().lower()
    model = str(payload.get("model") or "").strip() or None
    extra_instruction = str(payload.get("instructions") or "").strip()

    for index, variant in enumerate(variants):
        if variant.get("id") != variant_id:
            continue

        prompt = build_prompt(variant, extra_instruction=extra_instruction)

        used_ai = False
        error_message = ""

        if mode == "ollama":
            try:
                enhanced_body = ollama_generate(prompt, model=model)
                used_ai = True
            except (OSError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                enhanced_body = dry_run_enhancement(variant)
                error_message = str(exc)
        else:
            enhanced_body = dry_run_enhancement(variant)

        updated = dict(variant)
        updated["variant_body"] = enhanced_body
        updated["adaptation_mode"] = "ai_enhanced" if used_ai else "dry_run_enhanced"
        updated["status"] = "ready_for_review"
        updated["ai_enhanced_at"] = utc_now()
        updated["updated_at"] = utc_now()
        updated["ai_model"] = model or os.getenv("DAMA_OLLAMA_DEFAULT_MODEL", "qwen2.5-coder:7b")
        updated["ai_error"] = error_message
        updated["ai_prompt_preview"] = prompt[:1200]

        notes = updated.get("adaptation_notes")
        if not isinstance(notes, list):
            notes = []

        if used_ai:
            notes.append("نسخه با هوش مصنوعی برای کانال مقصد بهبود داده شد.")
        else:
            notes.append("نسخه با حالت امن dry-run آماده بازبینی شد.")

        if error_message:
            notes.append("Ollama در دسترس نبود یا خطا داد خروجی fallback ساخته شد.")

        updated["adaptation_notes"] = notes

        variants[index] = updated
        write_variants(variants)

        return {
            "ok": True,
            "used_ai": used_ai,
            "variant": updated,
            "message": "Variant enhanced with AI." if used_ai else "Variant enhanced with dry-run fallback.",
        }

    return None
