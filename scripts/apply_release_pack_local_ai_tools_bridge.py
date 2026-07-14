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


write_file(
    "backend/src/services/local_ai_tools_service.py",
    r'''
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
    ''',
)


api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "from typing import Any" not in api:
    api = "from typing import Any\n" + api

if "local_ai_tools_service" not in api:
    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\nfrom src.services.local_ai_tools_service import (\n    enhance_local_video_prompt,\n    local_ai_tools_status,\n)\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/local-tools/status")' not in api:
    api += r'''


@router.get("/local-tools/status")
def api_local_ai_tools_status() -> dict[str, Any]:
    return local_ai_tools_status()


@router.post("/local-video/prompt/enhance")
def api_enhance_local_video_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    return enhance_local_video_prompt(payload)
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with local AI tools endpoints.")


write_file(
    "backend/tests/smoke_test_local_ai_tools.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    status_response = client.get("/publishing/local-tools/status")
    assert status_response.status_code == 200, status_response.text
    status = status_response.json()
    assert "ollama" in status
    assert "comfyui" in status
    assert "local_video_command" in status

    enhance_response = client.post(
        "/publishing/local-video/prompt/enhance",
        json={
            "dry_run": True,
            "project_name": "DAMA Smoke",
            "title": "ویدیوی تست",
            "prompt": "حرکت آرام دوربین از روی تصویر شروع.",
            "duration_seconds": 4,
            "aspect_ratio": "16:9",
        },
    )
    assert enhance_response.status_code == 200, enhance_response.text
    payload = enhance_response.json()
    assert payload["ok"] is True
    assert payload["enhanced_prompt"]
    assert payload["negative_prompt"]

    print("Local AI tools smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


backend_check = ROOT / "scripts/backend-check.ps1"
backend_text = backend_check.read_text(encoding="utf-8")

if "smoke_test_local_ai_tools.py" not in backend_text:
    backend_text = backend_text.rstrip() + r'''

$LocalAIToolsSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_local_ai_tools.py"
$LocalAIToolsPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $LocalAIToolsSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_local_ai_tools.py..."
    & $LocalAIToolsPython $LocalAIToolsSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_local_ai_tools.py"
    }
}
''' + "\n"

    backend_check.write_text(backend_text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


write_file(
    "scripts/probe_local_ai_tools.py",
    r'''
from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT = Path("I:/DAMA")
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from src.services.local_ai_tools_service import local_ai_tools_status  # noqa: E402


def main() -> None:
    print(json.dumps(local_ai_tools_status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/create-local-video-job-form.tsx",
    r'''
"use client";

import { FormEvent, useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type CreateLocalVideoJobFormProps = {
  apiBaseUrl: string;
};

export function CreateLocalVideoJobForm({ apiBaseUrl }: CreateLocalVideoJobFormProps) {
  const [projectName, setProjectName] = useState("");
  const [title, setTitle] = useState("");
  const [startImage, setStartImage] = useState("");
  const [endImage, setEndImage] = useState("");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [duration, setDuration] = useState("4");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [fps, setFps] = useState("24");
  const [message, setMessage] = useState("");
  const [jobLink, setJobLink] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);

  async function handleEnhancePrompt() {
    setIsEnhancing(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/local-video/prompt/enhance`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          title,
          start_image: startImage,
          end_image: endImage,
          prompt,
          negative_prompt: negativePrompt,
          duration_seconds: Number(duration),
          aspect_ratio: aspectRatio,
          fps: Number(fps)
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      if (payload.enhanced_prompt) {
        setPrompt(String(payload.enhanced_prompt));
      }

      if (payload.negative_prompt) {
        setNegativePrompt(String(payload.negative_prompt));
      }

      setMessage(payload.message ?? "پرامپت بهبود داده شد.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsEnhancing(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");
    setJobLink("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/local-video/jobs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          title,
          start_image: startImage,
          end_image: endImage,
          prompt,
          negative_prompt: negativePrompt,
          duration_seconds: Number(duration),
          aspect_ratio: aspectRatio,
          fps: Number(fps)
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("درخواست ویدیو ساخته شد. حالا میتوانی dry-run بگیری یا موتور لوکال را اجرا کنی.");
      setJobLink(`/produce/video/${payload.id}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form local-video-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">ویدیو لوکال</p>
        <h2>ساخت درخواست ویدیو از تصویر</h2>
      </div>

      <label>
        پروژه
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="مثلا درخت و دختر دامامدیا اورماشاپ..."
        />
      </label>

      <label>
        عنوان ویدیو
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="مثلا حرکت آرام پوستر به نمای سینمایی"
        />
      </label>

      <label>
        تصویر شروع
        <input
          value={startImage}
          onChange={(event) => setStartImage(event.target.value)}
          placeholder="مسیر فایل یا لینک تصویر شروع مثل I:/DAMA/media/start.png"
          required
        />
      </label>

      <label>
        تصویر پایان اختیاری
        <input
          value={endImage}
          onChange={(event) => setEndImage(event.target.value)}
          placeholder="اگر لازم است مسیر تصویر پایان را وارد کن"
        />
      </label>

      <label>
        پرامپت حرکت
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="مثلا: حرکت آرام دوربین زوم نرم نور سینمایی تبدیل تدریجی به تصویر پایان..."
          rows={6}
          required
        />
      </label>

      <div className="actions">
        <button
          type="button"
          onClick={handleEnhancePrompt}
          disabled={isEnhancing || !prompt}
        >
          {isEnhancing ? "در حال بهبود..." : "بهبود پرامپت با Ollama/Qwen"}
        </button>
      </div>

      <label>
        پرامپت منفی اختیاری
        <textarea
          value={negativePrompt}
          onChange={(event) => setNegativePrompt(event.target.value)}
          placeholder="مثلا: لرزش زیاد تغییر چهره اعوجاج نوشته اضافه فریم خراب"
          rows={3}
        />
      </label>

      <div className="form-grid-3">
        <label>
          مدت ویدیو
          <input
            type="number"
            min="1"
            max="30"
            step="0.5"
            value={duration}
            onChange={(event) => setDuration(event.target.value)}
          />
        </label>

        <label>
          نسبت تصویر
          <select value={aspectRatio} onChange={(event) => setAspectRatio(event.target.value)}>
            <option value="16:9">افقی 16:9</option>
            <option value="9:16">عمودی 9:16</option>
            <option value="1:1">مربع 1:1</option>
            <option value="4:5">پست 4:5</option>
            <option value="3:4">عمودی 3:4</option>
            <option value="4:3">قدیمی 4:3</option>
          </select>
        </label>

        <label>
          فریمریت
          <input
            type="number"
            min="8"
            max="60"
            value={fps}
            onChange={(event) => setFps(event.target.value)}
          />
        </label>
      </div>

      <p className="muted-note">
        Ollama/Qwen پرامپت را بهتر میکند. ساخت واقعی ویدیو با موتور لوکال انجام میشود که باید جداگانه وصل شود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      {jobLink ? (
        <div className="actions">
          <a href={jobLink}>مشاهده درخواست ویدیو</a>
          <a href="/produce/video">درخواستهای ویدیو</a>
        </div>
      ) : null}

      <button type="submit" disabled={isSaving || !startImage || !prompt}>
        {isSaving ? "در حال ثبت..." : "ثبت درخواست ویدیو"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/app/produce/video/setup/page.tsx",
    r'''
import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";
import { labelReady } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadStatus(): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/local-tools/status`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return asRecord(await response.json());
  } catch {
    return {};
  }
}

export default async function LocalVideoSetupPage() {
  const status = await loadStatus();
  const ollama = asRecord(status.ollama);
  const comfyui = asRecord(status.comfyui);
  const localVideoCommand = asRecord(status.local_video_command);

  const models = Array.isArray(ollama.models) ? ollama.models.map(String) : [];
  const qwenModels = Array.isArray(ollama.qwen_models) ? ollama.qwen_models.map(String) : [];

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="ابزارهای لوکال"
        title="وضعیت Ollama Qwen و موتور ویدیو"
        lead="اینجا میبینی DAMA کدام ابزارهای لوکال را پیدا کرده و برای ساخت واقعی ویدیو چه چیزی کم است."
      >
        <div className="actions">
          <a href="/produce/video">بازگشت به ویدیو</a>
          <a href="/other">سایر</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Ollama" value={labelReady(Boolean(ollama.ready))} helper={String(ollama.message ?? "")} />
        <StatCard label="Qwen" value={qwenModels.length > 0 ? "پیدا شد" : "پیدا نشد"} helper={String(ollama.preferred_model ?? "")} />
        <StatCard label="ComfyUI" value={labelReady(Boolean(comfyui.ready))} helper={String(comfyui.base_url ?? "")} />
        <StatCard label="موتور ویدیو" value={labelReady(Boolean(localVideoCommand.ready))} helper={String(localVideoCommand.message ?? "")} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Ollama / Qwen</p>
            <h2>برای بهبود پرامپت</h2>
          </div>

          <dl className="detail-list">
            <div>
              <dt>آدرس</dt>
              <dd>{String(ollama.base_url ?? "")}</dd>
            </div>
            <div>
              <dt>مدل پیشنهادی</dt>
              <dd>{String(ollama.preferred_model ?? "")}</dd>
            </div>
            <div>
              <dt>مدلهای Qwen</dt>
              <dd>{qwenModels.length > 0 ? qwenModels.join(" ") : ""}</dd>
            </div>
            <div>
              <dt>همه مدلها</dt>
              <dd>{models.length > 0 ? models.join(" ") : ""}</dd>
            </div>
          </dl>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">موتور ویدیو</p>
            <h2>برای ساخت واقعی</h2>
          </div>

          <ol className="simple-steps">
            <li>Ollama/Qwen فقط پرامپت را بهتر میکند.</li>
            <li>برای ساخت واقعی ویدیو باید ComfyUI یا یک اسکریپت لوکال وصل شود.</li>
            <li>اگر آن برنامه Studio همان ComfyUI یا ابزار سازگار باشد از همین مسیر وصلش میکنیم.</li>
            <li>متغیر DAMA_LOCAL_VIDEO_COMMAND مسیر اسکریپت اجرای ویدیو را مشخص میکند.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی</summary>
          <pre className="json-block">{JSON.stringify(status, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
    ''',
)


video_page = ROOT / "frontend/src/app/produce/video/page.tsx"
video_text = video_page.read_text(encoding="utf-8")
if '/produce/video/setup' not in video_text:
    video_text = video_text.replace(
        '<a href="/other">سایر</a>',
        '<a href="/produce/video/setup">تنظیم ابزارهای لوکال</a>\n          <a href="/other">سایر</a>',
    )
video_page.write_text(video_text, encoding="utf-8")
print("Patched local video page with setup link.")


write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path -LiteralPath ".\frontend\node_modules")) {
    throw "frontend/node_modules not found. Run npm install in frontend first."
}

Write-Host "node_modules found. Running frontend typecheck..."

Push-Location ".\frontend"
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Frontend typecheck failed."
}
Pop-Location

$RequiredFiles = @(
    ".\frontend\src\components\create-local-video-job-form.tsx",
    ".\frontend\src\app\produce\video\page.tsx",
    ".\frontend\src\app\produce\video\setup\page.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$VideoForm = Read-TextFile ".\frontend\src\components\create-local-video-job-form.tsx"
$VideoPage = Read-TextFile ".\frontend\src\app\produce\video\page.tsx"
$SetupPage = Read-TextFile ".\frontend\src\app\produce\video\setup\page.tsx"

if ($VideoForm -notmatch "/publishing/local-video/prompt/enhance") {
    throw "Local video form is missing Ollama prompt enhancement endpoint."
}

if ($VideoForm -notmatch "Ollama/Qwen") {
    throw "Local video form is missing Ollama/Qwen visible action."
}

if ($VideoPage -notmatch "/produce/video/setup") {
    throw "Local video page is missing setup link."
}

if ($SetupPage -notmatch "/publishing/local-tools/status") {
    throw "Local video setup page does not call local tools status endpoint."
}

if ($SetupPage -notmatch "ComfyUI") {
    throw "Local video setup page does not mention ComfyUI detection."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-9 Completed",
    r'''
## Release Pack AI-9 Completed

Name:

Local AI Tools Bridge

Added files:

- backend/src/services/local_ai_tools_service.py
- backend/tests/smoke_test_local_ai_tools.py
- scripts/probe_local_ai_tools.py
- frontend/src/app/produce/video/setup/page.tsx

Updated files:

- backend/src/api/publishing.py
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- frontend/src/components/create-local-video-job-form.tsx
- frontend/src/app/produce/video/page.tsx
- docs/project-status.md

Added behavior:

- DAMA detects local Ollama
- DAMA lists Qwen models if available
- DAMA probes default ComfyUI local API
- DAMA checks DAMA_LOCAL_VIDEO_COMMAND
- local video form can enhance prompts with Ollama/Qwen
- fallback prompt enhancement works even if Ollama is offline
- local video setup page shows tool readiness

Next recommended step:

Release Pack AI-10: ComfyUI/Wan Adapter

Goal:

- decide which installed local studio/video engine will be used
- create a concrete adapter script for that engine
- set DAMA_LOCAL_VIDEO_COMMAND to that adapter
- run a real short 4-second image-to-video job locally
    ''',
)


print("Release Pack AI-9 applied successfully.")
