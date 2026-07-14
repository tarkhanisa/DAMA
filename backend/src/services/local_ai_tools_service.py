from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
import json
import os


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"


def http_json_get(url: str, timeout: float = 2.5) -> tuple[bool, Any, str]:
    try:
        with urlopen(url, timeout=timeout) as response:
            return True, json.loads(response.read().decode("utf-8")), ""
    except Exception as exc:
        return False, None, str(exc)


def http_json_post(url: str, payload: dict[str, Any], timeout: float = 60.0) -> tuple[bool, Any, str]:
    try:
        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=timeout) as response:
            return True, json.loads(response.read().decode("utf-8")), ""
    except Exception as exc:
        return False, None, str(exc)


def ollama_status() -> dict[str, Any]:
    base_url = os.getenv("DAMA_OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    ok, payload, error = http_json_get(f"{base_url}/api/tags")

    models: list[str] = []

    if ok and isinstance(payload, dict):
        raw_models = payload.get("models")
        if isinstance(raw_models, list):
            for item in raw_models:
                if isinstance(item, dict) and item.get("name"):
                    models.append(str(item["name"]))

    qwen_models = [name for name in models if "qwen" in name.lower()]
    configured_model = os.getenv("DAMA_OLLAMA_MODEL", "").strip()
    preferred_model = configured_model or (qwen_models[0] if qwen_models else "qwen2.5-coder:7b")

    return {
        "ready": ok and bool(models),
        "base_url": base_url,
        "models": models,
        "qwen_models": qwen_models,
        "preferred_model": preferred_model,
        "message": (
            "Ollama آماده است."
            if ok and models
            else "Ollama در دسترس نیست یا مدلی پیدا نشد."
        ),
        "error": "" if ok else error,
    }


def comfyui_status() -> dict[str, Any]:
    base_url = os.getenv("DAMA_COMFYUI_URL", DEFAULT_COMFYUI_URL).rstrip("/")
    ok, payload, error = http_json_get(f"{base_url}/system_stats", timeout=2.5)

    return {
        "ready": ok,
        "base_url": base_url,
        "message": (
            "ComfyUI یا ابزار سازگار با آن روی لوکال پاسخ میدهد."
            if ok
            else "ComfyUI روی آدرس پیشفرض پاسخ نداد."
        ),
        "error": "" if ok else error,
        "raw": payload if ok else {},
    }


def local_video_command_status() -> dict[str, Any]:
    command = os.getenv("DAMA_LOCAL_VIDEO_COMMAND", "").strip()
    output_dir = os.getenv("DAMA_LOCAL_VIDEO_OUTPUT_DIR", "").strip()

    return {
        "ready": bool(command),
        "command": command,
        "output_dir": output_dir,
        "message": (
            "دستور اجرای موتور ویدیو لوکال تنظیم شده است."
            if command
            else "هنوز DAMA_LOCAL_VIDEO_COMMAND تنظیم نشده است."
        ),
    }


def local_ai_tools_status() -> dict[str, Any]:
    ollama = ollama_status()
    comfyui = comfyui_status()
    local_video_command = local_video_command_status()

    return {
        "ok": True,
        "ollama": ollama,
        "comfyui": comfyui,
        "local_video_command": local_video_command,
        "recommended_next_step": (
            "از Qwen برای بهبود پرامپت استفاده کن برای ساخت واقعی ویدیو ComfyUI یا دستور لوکال را وصل کن."
        ),
    }


def fallback_video_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = str(payload.get("prompt") or "").strip()
    duration = str(payload.get("duration_seconds") or "4").strip()
    aspect_ratio = str(payload.get("aspect_ratio") or "16:9").strip()

    enhanced = (
        f"{prompt}\n\n"
        f"ویدیوی image-to-video به مدت {duration} ثانیه با نسبت تصویر {aspect_ratio}. "
        "حرکت دوربین نرم تغییرات تدریجی نورپردازی سینمایی حفظ هویت سوژه "
        "بدون پرش ناگهانی بدون اعوجاج و بدون تغییر ناخواسته در چهره یا فرم اصلی."
    ).strip()

    return {
        "ok": True,
        "mode": "fallback",
        "model": "",
        "enhanced_prompt": enhanced,
        "negative_prompt": (
            "flicker, jitter, distortion, warped face, extra limbs, text artifacts, "
            "logo, watermark, sudden camera jump, low quality, broken frame"
        ),
        "shot_plan": "شروع از تصویر اول حرکت نرم دوربین افزایش تدریجی عمق و نور پایان پایدار و خوانا.",
        "message": "پرامپت با الگوی داخلی بهبود داده شد.",
    }


def parse_jsonish_text(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def enhance_local_video_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    if bool(payload.get("dry_run")):
        result = fallback_video_prompt(payload)
        result["mode"] = "dry_run"
        result["message"] = "Dry-run پرامپت انجام شد."
        return result

    ollama = ollama_status()

    if not ollama["ready"]:
        result = fallback_video_prompt(payload)
        result["message"] = "Ollama در دسترس نبود پرامپت با الگوی داخلی بهبود داده شد."
        return result

    model = str(payload.get("model") or ollama["preferred_model"]).strip()
    user_prompt = str(payload.get("prompt") or "").strip()
    negative_prompt = str(payload.get("negative_prompt") or "").strip()
    duration = str(payload.get("duration_seconds") or "4").strip()
    aspect_ratio = str(payload.get("aspect_ratio") or "16:9").strip()
    title = str(payload.get("title") or "").strip()
    project_name = str(payload.get("project_name") or "").strip()

    instruction = f"""
تو یک پرامپتنویس حرفهای برای تولید ویدیوی image-to-video لوکال هستی.
خروجی را فقط JSON بده و هیچ توضیح اضافه ننویس.

اطلاعات:
- پروژه: {project_name}
- عنوان: {title}
- مدت: {duration} ثانیه
- نسبت تصویر: {aspect_ratio}
- پرامپت خام: {user_prompt}
- پرامپت منفی فعلی: {negative_prompt}

JSON با این کلیدها بده:
{{
  "enhanced_prompt": "پرامپت کامل دقیق سینمایی و مناسب image-to-video",
  "negative_prompt": "پرامپت منفی کوتاه و مفید",
  "shot_plan": "شرح بسیار کوتاه حرکت دوربین و اتفاقات ویدیو"
}}

قواعد:
- هویت تصویر شروع حفظ شود.
- اگر تصویر پایان وجود داشته باشد حرکت باید بهسمت آن طراحی شود.
- برای ویدیوی کوتاه  ثانیهای حرکتها باید نرم و محدود باشند.
- از اغراق پرش دوربین تغییر چهره و تغییر ناخواسته فرم اصلی پرهیز شود.
""".strip()

    ok, response, error = http_json_post(
        f"{ollama['base_url']}/api/generate",
        {
            "model": model,
            "prompt": instruction,
            "stream": False,
        },
        timeout=float(os.getenv("DAMA_OLLAMA_TIMEOUT_SECONDS", "90")),
    )

    if not ok or not isinstance(response, dict):
        result = fallback_video_prompt(payload)
        result["message"] = f"Ollama پاسخ نداد fallback استفاده شد. {error}"
        return result

    raw_text = str(response.get("response") or "").strip()
    parsed = parse_jsonish_text(raw_text)

    if not parsed:
        result = fallback_video_prompt(payload)
        result["mode"] = "ollama_fallback"
        result["model"] = model
        result["raw"] = raw_text
        result["message"] = "خروجی Qwen قابل تبدیل به JSON نبود fallback استفاده شد."
        return result

    return {
        "ok": True,
        "mode": "ollama",
        "model": model,
        "enhanced_prompt": str(parsed.get("enhanced_prompt") or "").strip() or fallback_video_prompt(payload)["enhanced_prompt"],
        "negative_prompt": str(parsed.get("negative_prompt") or "").strip() or fallback_video_prompt(payload)["negative_prompt"],
        "shot_plan": str(parsed.get("shot_plan") or "").strip(),
        "message": "پرامپت با Ollama/Qwen بهبود داده شد.",
        "raw": raw_text,
    }
