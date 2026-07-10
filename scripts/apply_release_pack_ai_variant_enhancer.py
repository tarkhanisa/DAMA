from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


def patch_backend_check() -> None:
    target = ROOT / "scripts/backend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "smoke_test_publishing_ai_enhancer.py" in text:
        print("Skipped backend-check patch.")
        return

    if '"./backend/tests/smoke_test_publishing_variants.py"' in text:
        text = text.replace(
            '"./backend/tests/smoke_test_publishing_variants.py"',
            '"./backend/tests/smoke_test_publishing_variants.py",\n    "./backend/tests/smoke_test_publishing_ai_enhancer.py"',
            1,
        )
    elif '".\\backend\\tests\\smoke_test_publishing_variants.py"' in text:
        text = text.replace(
            '".\\backend\\tests\\smoke_test_publishing_variants.py"',
            '".\\backend\\tests\\smoke_test_publishing_variants.py",\n    ".\\backend\\tests\\smoke_test_publishing_ai_enhancer.py"',
            1,
        )
    else:
        text = text.rstrip() + r'''

$PublishingAiSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_publishing_ai_enhancer.py"
$PublishingAiPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $PublishingAiSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_publishing_ai_enhancer.py..."
    & $PublishingAiPython $PublishingAiSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_publishing_ai_enhancer.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\components\\enhance-publishing-variant-action.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\components\\create-publishing-variants-form.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Publishing variant enhancer action is missing enhance endpoint." not in text:
        block = r'''
$PublishingEnhancerAction = Read-TextFile ".\frontend\src\components\enhance-publishing-variant-action.tsx"

if ($PublishingEnhancerAction -notmatch "/publishing/variants/") {
    throw "Publishing variant enhancer action is missing variant endpoint."
}

if ($PublishingEnhancerAction -notmatch "/enhance") {
    throw "Publishing variant enhancer action is missing enhance endpoint."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "backend/src/services/publishing_variant_ai_service.py",
    r'''
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
    ''',
)


# Patch publishing API to include enhancer imports/endpoints.
publishing_api = ROOT / "backend/src/api/publishing.py"
text = publishing_api.read_text(encoding="utf-8")

if "from src.services.publishing_variant_ai_service import enhance_variant" not in text:
    text = text.replace(
        "from src.services.publishing_variant_service import (",
        "from src.services.publishing_variant_ai_service import enhance_variant\nfrom src.services.publishing_variant_service import (",
        1,
    )

if '@router.post("/variants/{variant_id}/enhance")' not in text:
    text = text.rstrip() + r'''


@router.post("/variants/{variant_id}/enhance")
def api_enhance_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = enhance_variant(variant_id, payload)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return result
''' + "\n"

publishing_api.write_text(text.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py")


write_file(
    "backend/tests/smoke_test_publishing_ai_enhancer.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA AI Enhancer Telegram",
            "channel_type": "telegram",
            "target_url": "@example",
            "notes": "AI enhancer smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-ai-content-asset",
            "source_title": "تست بهبود نسخه کانالی",
            "source_body": "این متن مادر برای بررسی بهبود نسخه کانالی با حالت dry run استفاده میشود.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    enhance_response = client.post(
        f"/publishing/variants/{variant['id']}/enhance",
        json={
            "mode": "dry_run",
            "instructions": "خروجی را کوتاه و خوانا کن.",
        },
    )
    assert enhance_response.status_code == 200, enhance_response.text

    payload = enhance_response.json()
    assert payload["ok"] is True
    assert payload["used_ai"] is False
    assert payload["variant"]["status"] == "ready_for_review"
    assert payload["variant"]["variant_body"]

    print("Publishing AI enhancer smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/enhance-publishing-variant-action.tsx",
    r'''
"use client";

import { useState } from "react";

type EnhancePublishingVariantActionProps = {
  apiBaseUrl: string;
  variantId: string;
};

export function EnhancePublishingVariantAction({
  apiBaseUrl,
  variantId
}: EnhancePublishingVariantActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [instructions, setInstructions] = useState("");
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [message, setMessage] = useState("");

  async function handleEnhance() {
    setIsEnhancing(true);
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/enhance`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            mode,
            instructions
          })
        }
      );

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در بهبود نسخه: HTTP ${response.status}`);
        return;
      }

      setMessage(
        payload.used_ai
          ? "نسخه با AI بهبود داده شد. صفحه را refresh کن."
          : "نسخه با حالت امن dry-run آماده بازبینی شد. صفحه را refresh کن."
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsEnhancing(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <label>
        حالت بهبود
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="dry_run">Dry-run امن</option>
          <option value="ollama">Ollama AI</option>
        </select>
      </label>

      <label>
        دستور تکمیلی
        <input
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
          placeholder="مثلا رسمیتر کوتاهتر مناسب تلگرام بدون ایموجی"
        />
      </label>

      <button type="button" onClick={handleEnhance} disabled={isEnhancing}>
        {isEnhancing ? "در حال بهبود..." : "بهبود نسخه"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
    ''',
)


# Patch variants page: import action and show action for rows.
variants_page = ROOT / "frontend/src/app/publishing/variants/page.tsx"
page = variants_page.read_text(encoding="utf-8")

if 'import { EnhancePublishingVariantAction }' not in page:
    page = page.replace(
        'import { CreatePublishingVariantsForm } from "../../../components/create-publishing-variants-form";',
        'import { CreatePublishingVariantsForm } from "../../../components/create-publishing-variants-form";\nimport { EnhancePublishingVariantAction } from "../../../components/enhance-publishing-variant-action";',
        1,
    )

if "<th>اقدام</th>" not in page:
    page = page.replace(
        "<th>وضعیت</th>",
        "<th>وضعیت</th>\n                <th>اقدام</th>",
        1,
    )
    page = page.replace(
        """<td>
                      <span className={`status-badge status-${variant.status}`}>
                        {variant.status}
                      </span>
                    </td>""",
        """<td>
                      <span className={`status-badge status-${variant.status}`}>
                        {variant.status}
                      </span>
                    </td>
                    <td>
                      <EnhancePublishingVariantAction
                        apiBaseUrl={API_BASE_URL}
                        variantId={variant.id}
                      />
                    </td>""",
        1,
    )
    page = page.replace(
        '<td colSpan={4}>هنوز نسخهای ساخته نشده است.</td>',
        '<td colSpan={5}>هنوز نسخهای ساخته نشده است.</td>',
        1,
    )

variants_page.write_text(page, encoding="utf-8")
print("Patched frontend/src/app/publishing/variants/page.tsx")


append_once(
    "frontend/src/app/globals.css",
    "/* AI variant enhancer */",
    r'''
/* AI variant enhancer */
.enhance-variant-action {
  display: grid;
  gap: 0.5rem;
  min-width: 14rem;
}

.enhance-variant-action label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: var(--muted);
}

.enhance-variant-action input,
.enhance-variant-action select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 0.7rem;
  padding: 0.55rem 0.7rem;
  background: rgba(255, 255, 255, 0.78);
  color: var(--text);
  font: inherit;
}

.enhance-variant-action button {
  border: 0;
  border-radius: 999px;
  padding: 0.6rem 0.9rem;
  font-weight: 800;
  cursor: pointer;
  background: var(--text);
  color: var(--surface);
}

.enhance-variant-action button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
    ''',
)


append_once(
    "docs/publishing-foundation.md",
    "## AI Variant Enhancer",
    r'''
## AI Variant Enhancer

Release Pack Y adds an enhancement endpoint for publishing variants.

Endpoint:

    POST /publishing/variants/{variant_id}/enhance

Modes:

- dry_run
- ollama

Dry-run mode is safe and does not require Ollama.

Ollama mode tries to rewrite the variant for the selected channel. If Ollama is unreachable, the backend falls back to a safe dry-run enhancement and records the error.

This step still does not publish anything.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack Y Completed",
    r'''
## Release Pack Y Completed

Name:

AI Variant Enhancer

Added files:

- backend/src/services/publishing_variant_ai_service.py
- backend/tests/smoke_test_publishing_ai_enhancer.py
- frontend/src/components/enhance-publishing-variant-action.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/page.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- enhance publishing variant endpoint
- dry-run enhancement
- Ollama enhancement mode
- channel-specific rewrite prompts
- safe fallback when Ollama is unavailable
- frontend action to enhance a variant

Next recommended Release Pack:

Release Pack Z: Publishing Review + Approval Workflow

Suggested scope:

- variant detail page
- approve/reject variant
- ready_for_publish status
- review notes
- compare source vs variant
- no real publishing yet
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack Y applied successfully.")
