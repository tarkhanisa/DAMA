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
    "backend/src/services/local_video_service.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json
import os
import subprocess


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
JOBS_PATH = DATA_DIR / "local_video_jobs.json"
OUTPUT_ROOT = Path(os.getenv("DAMA_LOCAL_VIDEO_OUTPUT_DIR", str(BACKEND_ROOT / "outputs" / "local-video")))

ALLOWED_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:5", "3:4", "4:3"}
ALLOWED_STATUSES = {"draft", "queued", "running", "dry_run", "blocked", "completed", "failed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    if not JOBS_PATH.exists():
        JOBS_PATH.write_text("[]\n", encoding="utf-8")


def read_jobs() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_jobs(items: list[dict[str, Any]]) -> None:
    ensure_store()
    JOBS_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_duration(value: Any) -> float:
    try:
        duration = float(value)
    except (TypeError, ValueError):
        duration = 4.0

    return max(1.0, min(duration, 30.0))


def normalize_fps(value: Any) -> int:
    try:
        fps = int(value)
    except (TypeError, ValueError):
        fps = 24

    return max(8, min(fps, 60))


def normalize_aspect_ratio(value: Any) -> str:
    aspect_ratio = str(value or "16:9").strip()

    return aspect_ratio if aspect_ratio in ALLOWED_ASPECT_RATIOS else "16:9"


def local_video_config() -> dict[str, Any]:
    command = os.getenv("DAMA_LOCAL_VIDEO_COMMAND", "").strip()

    return {
        "ready": bool(command),
        "mode": "external_command" if command else "dry_run_only",
        "command_configured": bool(command),
        "output_dir": str(OUTPUT_ROOT),
        "message": (
            "ابزار ویدیو لوکال تنظیم شده است."
            if command
            else "هنوز دستور اجرای ابزار ویدیو لوکال تنظیم نشده است. فعلاً فقط job و dry-run ساخته می‌شود."
        ),
        "env_keys": [
            "DAMA_LOCAL_VIDEO_COMMAND",
            "DAMA_LOCAL_VIDEO_OUTPUT_DIR",
        ],
    }


def list_video_jobs(status: str | None = None) -> dict[str, Any]:
    items = read_jobs()

    if status:
        items = [item for item in items if item.get("status") == status]

    return {
        "total": len(items),
        "items": items,
    }


def get_video_job(job_id: str) -> dict[str, Any] | None:
    for item in read_jobs():
        if item.get("id") == job_id:
            return item

    return None


def update_job(job_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    items = read_jobs()

    for index, item in enumerate(items):
        if item.get("id") != job_id:
            continue

        updated = dict(item)
        updated.update(updates)
        updated["updated_at"] = utc_now()

        history = updated.get("history")
        if not isinstance(history, list):
            history = []

        if "status" in updates:
            history.append(
                {
                    "status": updates["status"],
                    "at": updated["updated_at"],
                    "message": str(updates.get("history_message") or ""),
                }
            )

        updated["history"] = history
        updated.pop("history_message", None)

        items[index] = updated
        write_jobs(items)

        return updated

    return None


def create_video_job(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()

    prompt = str(payload.get("prompt") or "").strip()
    start_image = str(payload.get("start_image") or "").strip()
    end_image = str(payload.get("end_image") or "").strip()

    job = {
        "id": str(uuid4()),
        "project_name": str(payload.get("project_name") or "").strip(),
        "title": str(payload.get("title") or "ویدیوی لوکال").strip(),
        "prompt": prompt,
        "negative_prompt": str(payload.get("negative_prompt") or "").strip(),
        "start_image": start_image,
        "end_image": end_image,
        "duration_seconds": normalize_duration(payload.get("duration_seconds")),
        "aspect_ratio": normalize_aspect_ratio(payload.get("aspect_ratio")),
        "fps": normalize_fps(payload.get("fps")),
        "seed": str(payload.get("seed") or "").strip(),
        "profile": str(payload.get("profile") or "image-to-video").strip(),
        "status": "draft",
        "output_path": "",
        "error": "",
        "created_at": now,
        "updated_at": now,
        "history": [
            {
                "status": "draft",
                "at": now,
                "message": "Local video job created.",
            }
        ],
    }

    if not prompt:
        job["status"] = "blocked"
        job["error"] = "Prompt is required."

    if not start_image:
        job["status"] = "blocked"
        job["error"] = "Start image is required."

    items = read_jobs()
    items.insert(0, job)
    write_jobs(items)

    return job


def job_input_path(job: dict[str, Any]) -> Path:
    job_dir = OUTPUT_ROOT / str(job["id"])
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir / "input.json"


def job_output_path(job: dict[str, Any]) -> Path:
    job_dir = OUTPUT_ROOT / str(job["id"])
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir / "output.mp4"


def run_video_job(job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    job = get_video_job(job_id)

    if not job:
        return None

    request = payload or {}
    mode = str(request.get("mode") or "dry_run").strip()

    if job.get("status") == "blocked":
        return {
            "ok": False,
            "job": job,
            "message": job.get("error") or "Job is blocked.",
        }

    if mode == "dry_run":
        input_path = job_input_path(job)
        input_path.write_text(
            json.dumps(job, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        updated = update_job(
            job_id,
            {
                "status": "dry_run",
                "output_path": "",
                "error": "",
                "history_message": "Dry-run completed. Input JSON prepared.",
            },
        )

        return {
            "ok": True,
            "job": updated,
            "message": "Dry-run انجام شد. فایل ورودی ابزار لوکال آماده شد.",
            "input_path": str(input_path),
        }

    command = os.getenv("DAMA_LOCAL_VIDEO_COMMAND", "").strip()

    if not command:
        updated = update_job(
            job_id,
            {
                "status": "blocked",
                "error": "DAMA_LOCAL_VIDEO_COMMAND is not configured.",
                "history_message": "Local video command is missing.",
            },
        )

        return {
            "ok": False,
            "job": updated,
            "message": "دستور اجرای ابزار ویدیوی لوکال تنظیم نشده است.",
        }

    input_path = job_input_path(job)
    output_path = job_output_path(job)

    input_path.write_text(
        json.dumps(job, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    update_job(
        job_id,
        {
            "status": "running",
            "error": "",
            "history_message": "Local video command started.",
        },
    )

    try:
        completed = subprocess.run(
            [
                command,
                str(input_path),
                str(output_path),
            ],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            timeout=int(os.getenv("DAMA_LOCAL_VIDEO_TIMEOUT_SECONDS", "1800")),
            check=False,
        )

        if completed.returncode != 0:
            updated = update_job(
                job_id,
                {
                    "status": "failed",
                    "error": (completed.stderr or completed.stdout or "Local video command failed.")[:4000],
                    "history_message": "Local video command failed.",
                },
            )

            return {
                "ok": False,
                "job": updated,
                "message": "اجرای ابزار ویدیو لوکال ناموفق بود.",
            }

        updated = update_job(
            job_id,
            {
                "status": "completed",
                "output_path": str(output_path),
                "error": "",
                "history_message": "Local video command completed.",
            },
        )

        return {
            "ok": True,
            "job": updated,
            "message": "ویدیو ساخته شد.",
            "output_path": str(output_path),
        }

    except Exception as exc:
        updated = update_job(
            job_id,
            {
                "status": "failed",
                "error": str(exc),
                "history_message": "Local video command crashed.",
            },
        )

        return {
            "ok": False,
            "job": updated,
            "message": str(exc),
        }
    ''',
)


api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "local_video_service" not in api:
    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\nfrom src.services.local_video_service import (\n    create_video_job,\n    get_video_job,\n    list_video_jobs,\n    local_video_config,\n    run_video_job,\n)\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/local-video/config")' not in api:
    api += r'''


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
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with local video endpoints.")


write_file(
    "backend/tests/smoke_test_local_video.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    config_response = client.get("/publishing/local-video/config")
    assert config_response.status_code == 200, config_response.text

    create_response = client.post(
        "/publishing/local-video/jobs",
        json={
            "project_name": "DAMA Smoke",
            "title": "تست ویدیو لوکال",
            "start_image": "I:/DAMA/smoke-start.png",
            "end_image": "I:/DAMA/smoke-end.png",
            "prompt": "حرکت آرام سینمایی از تصویر اول به تصویر دوم.",
            "duration_seconds": 4,
            "aspect_ratio": "16:9",
            "fps": 24,
        },
    )
    assert create_response.status_code == 200, create_response.text
    job = create_response.json()
    assert job["id"]
    assert job["duration_seconds"] == 4
    assert job["aspect_ratio"] == "16:9"

    run_response = client.post(
        f"/publishing/local-video/jobs/{job['id']}/run",
        json={"mode": "dry_run"},
    )
    assert run_response.status_code == 200, run_response.text
    payload = run_response.json()
    assert payload["ok"] is True
    assert payload["job"]["status"] == "dry_run"

    print("Local video smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


backend_check = ROOT / "scripts/backend-check.ps1"
backend_text = backend_check.read_text(encoding="utf-8")

if "smoke_test_local_video.py" not in backend_text:
    backend_text = backend_text.rstrip() + r'''

$LocalVideoSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_local_video.py"
$LocalVideoPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $LocalVideoSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_local_video.py..."
    & $LocalVideoPython $LocalVideoSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_local_video.py"
    }
}
''' + "\n"

    backend_check.write_text(backend_text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


write_file(
    "frontend/src/components/plan-campaign-variants-action.tsx",
    r'''
"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type PlanCampaignVariantsActionProps = {
  apiBaseUrl: string;
  campaignId: string;
  sourceTitle: string;
  sourceBody: string;
  channelIds: string[];
};

export function PlanCampaignVariantsAction({
  apiBaseUrl,
  campaignId,
  sourceTitle,
  sourceBody,
  channelIds
}: PlanCampaignVariantsActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function handlePlan() {
    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/variants/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content_asset_id: campaignId,
          source_title: sourceTitle,
          source_body: sourceBody,
          channel_ids: channelIds
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      await fetch(`${apiBaseUrl}/publishing/campaigns/${campaignId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status: "variant_planned",
          notes: "variants planned from campaign detail"
        })
      });

      const count = Array.isArray(payload.items) ? payload.items.length : 0;
      setMessage(`نسخه‌سازی انجام شد. تعداد نسخه‌ها: ${count}.`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <button type="button" onClick={handlePlan} disabled={isRunning || channelIds.length === 0}>
        {isRunning ? "در حال نسخه‌سازی..." : "ساخت نسخه برای کانال‌ها"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
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

      setMessage("درخواست ویدیو ساخته شد. فعلاً می‌توانی dry-run بگیری یا بعداً موتور لوکال را وصل کنیم.");
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
          placeholder="مثلاً درخت و دختر، دامامدیا، اورماشاپ..."
        />
      </label>

      <label>
        عنوان ویدیو
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="مثلاً حرکت آرام پوستر به نمای سینمایی"
        />
      </label>

      <label>
        تصویر شروع
        <input
          value={startImage}
          onChange={(event) => setStartImage(event.target.value)}
          placeholder="مسیر فایل یا لینک تصویر شروع، مثل I:/DAMA/media/start.png"
          required
        />
      </label>

      <label>
        تصویر پایان، اختیاری
        <input
          value={endImage}
          onChange={(event) => setEndImage(event.target.value)}
          placeholder="اگر لازم است، مسیر تصویر پایان را وارد کن"
        />
      </label>

      <label>
        پرامپت حرکت
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="مثلاً: حرکت آرام دوربین، زوم نرم، نور سینمایی، تبدیل تدریجی به تصویر پایان..."
          rows={6}
          required
        />
      </label>

      <label>
        پرامپت منفی، اختیاری
        <textarea
          value={negativePrompt}
          onChange={(event) => setNegativePrompt(event.target.value)}
          placeholder="مثلاً: لرزش زیاد، تغییر چهره، اعوجاج، نوشته اضافه، فریم خراب"
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
          فریم‌ریت
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
        پیش‌فرض مدت ویدیو ۴ ثانیه است. برای ساخت واقعی باید بعداً موتور لوکال را به DAMA وصل کنیم.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      {jobLink ? (
        <div className="actions">
          <a href={jobLink}>مشاهده درخواست ویدیو</a>
          <a href="/produce/video">درخواست‌های ویدیو</a>
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
    "frontend/src/components/run-local-video-job-action.tsx",
    r'''
"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type RunLocalVideoJobActionProps = {
  apiBaseUrl: string;
  jobId: string;
};

export function RunLocalVideoJobAction({ apiBaseUrl, jobId }: RunLocalVideoJobActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function run(mode: "dry_run" | "local") {
    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/local-video/jobs/${jobId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ mode })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage(payload.message ?? "اجرا انجام شد.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action local-video-actions">
      <button type="button" onClick={() => run("dry_run")} disabled={isRunning}>
        {isRunning ? "در حال اجرا..." : "Dry-run امن"}
      </button>

      <button type="button" onClick={() => run("local")} disabled={isRunning}>
        اجرای موتور لوکال
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/app/produce/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function ProducePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید"
        title="چه چیزی می‌خواهی بسازی؟"
        lead="تولید محتوا از اینجا شروع می‌شود. تولید متن فعال است و ابزار ویدیو لوکال هم به‌صورت پایه اضافه شده است."
      >
        <div className="actions">
          <a href="/generate">تولید متن</a>
          <a href="/produce/video">ویدیو لوکال</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="متن و پست" value="فعال" helper="با موتور فعلی تولید محتوا" />
        <StatCard label="ویدیو لوکال" value="پایه" helper="تصویر + پرامپت + تنظیمات" />
        <StatCard label="تصویر" value="بعدی" helper="در فاز تولید رسانه" />
        <StatCard label="پروژه" value="محور اصلی" helper="هر تولید باید به پروژه وصل شود" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/generate">
          <span>۱</span>
          <strong>تولید متن / پست</strong>
          <p>برای سایت، تلگرام، لینکدین یا کمپین، متن مادر بساز.</p>
        </a>

        <a className="operator-card primary-operator-card" href="/produce/video">
          <span>۲</span>
          <strong>تولید ویدیو لوکال</strong>
          <p>تصویر شروع، تصویر پایان اختیاری و پرامپت بده؛ درخواست ویدیو بساز.</p>
        </a>

        <a className="operator-card muted-operator-card" href="/produce">
          <span>۳</span>
          <strong>تولید تصویر</strong>
          <p>در مرحله بعد، تولید تصویر پروژه‌محور از اینجا فعال می‌شود.</p>
        </a>

        <a className="operator-card" href="/projects">
          <span>۴</span>
          <strong>پروژه‌ها</strong>
          <p>پروژه‌هایی که قبلاً تعریف شده‌اند را ببین.</p>
        </a>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/produce/video/page.tsx",
    r'''
import { CreateLocalVideoJobForm } from "../../../components/create-local-video-job-form";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { formatPersianDate } from "../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type LocalVideoJob = {
  id: string;
  project_name: string;
  title: string;
  status: string;
  duration_seconds: number;
  aspect_ratio: string;
  created_at: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getItems(payload: unknown): Record<string, unknown>[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return source.map(asRecord);
}

async function loadJson(path: string): Promise<unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return await response.json();
  } catch {
    return {};
  }
}

function normalizeJobs(payload: unknown): LocalVideoJob[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      project_name: String(item.project_name ?? ""),
      title: String(item.title ?? ""),
      status: String(item.status ?? ""),
      duration_seconds: Number(item.duration_seconds ?? 0),
      aspect_ratio: String(item.aspect_ratio ?? ""),
      created_at: String(item.created_at ?? "")
    }))
    .filter((item) => item.id);
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "ثبت‌شده",
    dry_run: "Dry-run انجام شد",
    blocked: "نیازمند تنظیم",
    running: "در حال اجرا",
    completed: "ساخته شد",
    failed: "خطا"
  };

  return labels[status] ?? "نامشخص";
}

export default async function LocalVideoPage() {
  const [configPayload, jobsPayload] = await Promise.all([
    loadJson("/publishing/local-video/config"),
    loadJson("/publishing/local-video/jobs")
  ]);

  const config = asRecord(configPayload);
  const jobs = normalizeJobs(jobsPayload);
  const ready = Boolean(config.ready);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید ویدیو لوکال"
        title="ویدیو از تصویر و پرامپت"
        lead="تصویر شروع را بده، اگر لازم بود تصویر پایان را هم بده، پرامپت حرکت را بنویس و مدت/نسبت تصویر را تنظیم کن."
      >
        <div className="actions">
          <a href="/produce">بازگشت به تولید</a>
          <a href="/other">سایر</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت موتور" value={ready ? "آماده" : "تنظیم نشده"} helper={String(config.message ?? "—")} />
        <StatCard label="مدت پیش‌فرض" value="۴ ثانیه" helper="قابل تغییر از فرم" />
        <StatCard label="نسبت تصویر" value="چندحالته" helper="16:9، 9:16، 1:1 و..." />
        <StatCard label="درخواست‌ها" value={jobs.length} helper="jobهای ثبت‌شده" />
      </section>

      <section className="two-column">
        <CreateLocalVideoJobForm apiBaseUrl={API_BASE_URL} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>این ابزار چه کار می‌کند؟</h2>
          </div>

          <ol className="simple-steps">
            <li>فعلاً درخواست ویدیو را استاندارد ثبت می‌کند.</li>
            <li>Dry-run فایل ورودی ابزار لوکال را می‌سازد.</li>
            <li>برای ساخت واقعی باید موتور لوکال را از طریق env وصل کنیم.</li>
            <li>بعداً می‌توانیم ComfyUI یا ابزار مشابه را به همین صفحه وصل کنیم.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">درخواست‌های اخیر</p>
          <h2>ویدیوهای ثبت‌شده</h2>
        </div>

        <div className="campaign-grid">
          {jobs.length > 0 ? (
            jobs.slice(0, 40).map((job) => (
              <a className="campaign-card" href={`/produce/video/${job.id}`} key={job.id}>
                <span className={`status-badge status-${job.status}`}>
                  {statusLabel(job.status)}
                </span>
                <strong>{job.title || "ویدیوی بدون عنوان"}</strong>
                <p>{job.project_name || "بدون پروژه"}</p>
                <dl>
                  <div>
                    <dt>مدت</dt>
                    <dd>{job.duration_seconds} ثانیه</dd>
                  </div>
                  <div>
                    <dt>نسبت</dt>
                    <dd>{job.aspect_ratio}</dd>
                  </div>
                  <div>
                    <dt>زمان</dt>
                    <dd>{formatPersianDate(job.created_at)}</dd>
                  </div>
                </dl>
              </a>
            ))
          ) : (
            <p className="muted-note">هنوز درخواست ویدیویی ثبت نشده است.</p>
          )}
        </div>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/produce/video/[jobId]/page.tsx",
    r'''
import { PageHeader } from "../../../../components/page-header";
import { RunLocalVideoJobAction } from "../../../../components/run-local-video-job-action";
import { StatCard } from "../../../../components/stat-card";
import { formatPersianDate, shortId } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type Props = {
  params: Promise<{
    jobId: string;
  }>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadJob(jobId: string): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/local-video/jobs/${jobId}`, {
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

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "ثبت‌شده",
    dry_run: "Dry-run انجام شد",
    blocked: "نیازمند تنظیم",
    running: "در حال اجرا",
    completed: "ساخته شد",
    failed: "خطا"
  };

  return labels[status] ?? "نامشخص";
}

export default async function LocalVideoJobPage({ params }: Props) {
  const { jobId } = await params;
  const job = await loadJob(jobId);

  const status = String(job.status ?? "");
  const outputPath = String(job.output_path ?? "");
  const error = String(job.error ?? "");

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="درخواست ویدیو"
        title={String(job.title ?? "ویدیوی لوکال")}
        lead={String(job.prompt ?? "درخواست تولید ویدیو از تصویر و پرامپت.")}
      >
        <div className="actions">
          <a href="/produce/video">بازگشت به ویدیوها</a>
          <a href="/produce">تولید</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(status)} helper={`شناسه: ${shortId(jobId)}`} />
        <StatCard label="مدت" value={`${String(job.duration_seconds ?? "۴")} ثانیه`} helper="قابل تنظیم در فرم" />
        <StatCard label="نسبت تصویر" value={String(job.aspect_ratio ?? "16:9")} helper={`FPS: ${String(job.fps ?? "24")}`} />
        <StatCard label="زمان ساخت" value={formatPersianDate(String(job.created_at ?? ""))} helper={String(job.project_name ?? "—")} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">پرامپت</p>
            <h2>حرکت و حس ویدیو</h2>
          </div>

          <div className="generated-output">
            <p>{String(job.prompt ?? "بدون پرامپت")}</p>
          </div>

          <dl className="detail-list">
            <div>
              <dt>تصویر شروع</dt>
              <dd>{String(job.start_image ?? "—")}</dd>
            </div>
            <div>
              <dt>تصویر پایان</dt>
              <dd>{String(job.end_image ?? "—") || "—"}</dd>
            </div>
            <div>
              <dt>خروجی</dt>
              <dd>{outputPath || "هنوز ساخته نشده"}</dd>
            </div>
            <div>
              <dt>خطا</dt>
              <dd>{error || "—"}</dd>
            </div>
          </dl>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">اجرا</p>
            <h2>Dry-run یا موتور لوکال</h2>
          </div>

          <p className="muted-note">
            Dry-run امن است و فقط فایل ورودی را آماده می‌کند. اجرای موتور لوکال وقتی کار می‌کند که
            DAMA_LOCAL_VIDEO_COMMAND تنظیم شده باشد.
          </p>

          <RunLocalVideoJobAction apiBaseUrl={API_BASE_URL} jobId={jobId} />
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی</summary>
          <pre className="json-block">{JSON.stringify(job, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
    ''',
)


campaign_detail = ROOT / "frontend/src/app/publishing/campaigns/[campaignId]/page.tsx"
campaign_text = campaign_detail.read_text(encoding="utf-8")

if "PlanCampaignVariantsAction" not in campaign_text:
    campaign_text = campaign_text.replace(
        'import { PageHeader } from "../../../../components/page-header";',
        'import { PageHeader } from "../../../../components/page-header";\nimport { PlanCampaignVariantsAction } from "../../../../components/plan-campaign-variants-action";',
    )

    marker = r'''
        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">قدم بعدی</p>
            <h2>بعد از ساخت کمپین</h2>
          </div>
'''
    replacement = r'''
        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">قدم بعدی</p>
            <h2>ساخت نسخه‌های کانالی</h2>
          </div>

          <PlanCampaignVariantsAction
            apiBaseUrl={API_BASE_URL}
            campaignId={campaignId}
            sourceTitle={String(campaign.source_title ?? "")}
            sourceBody={String(campaign.source_body ?? "")}
            channelIds={channelIds}
          />
'''
    if marker in campaign_text:
        campaign_text = campaign_text.replace(marker, replacement, 1)

    campaign_detail.write_text(campaign_text, encoding="utf-8")
    print("Patched campaign detail with variants planner action.")


append_once(
    "frontend/src/app/globals.css",
    "/* Local video composer */",
    r'''
/* Local video composer */
.local-video-form {
  border-color: rgba(35, 74, 112, 0.22);
}

.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
}

.local-video-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.local-video-actions button {
  min-height: 2.75rem;
}

@media (max-width: 780px) {
  .form-grid-3 {
    grid-template-columns: 1fr;
  }
}
    ''',
)


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
    ".\frontend\src\components\plan-campaign-variants-action.tsx",
    ".\frontend\src\components\create-local-video-job-form.tsx",
    ".\frontend\src\components\run-local-video-job-action.tsx",
    ".\frontend\src\app\produce\page.tsx",
    ".\frontend\src\app\produce\video\page.tsx",
    ".\frontend\src\app\produce\video\[jobId]\page.tsx",
    ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$ProducePage = Read-TextFile ".\frontend\src\app\produce\page.tsx"
$VideoPage = Read-TextFile ".\frontend\src\app\produce\video\page.tsx"
$VideoJobPage = Read-TextFile ".\frontend\src\app\produce\video\[jobId]\page.tsx"
$VideoForm = Read-TextFile ".\frontend\src\components\create-local-video-job-form.tsx"
$CampaignDetail = Read-TextFile ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx"
$PlanAction = Read-TextFile ".\frontend\src\components\plan-campaign-variants-action.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($ProducePage -notmatch "/produce/video") {
    throw "Produce page does not link to local video tool."
}

if ($VideoPage -notmatch "/publishing/local-video/jobs") {
    throw "Local video page does not call jobs endpoint."
}

if ($VideoJobPage -notmatch "RunLocalVideoJobAction") {
    throw "Local video detail page is missing run action."
}

if ($VideoForm -notmatch "duration_seconds") {
    throw "Local video form does not submit duration."
}

if ($VideoForm -notmatch "aspect_ratio") {
    throw "Local video form does not submit aspect ratio."
}

if ($CampaignDetail -notmatch "PlanCampaignVariantsAction") {
    throw "Campaign detail is missing variants planner action."
}

if ($PlanAction -notmatch "/publishing/variants/plan") {
    throw "Plan campaign variants action does not call variants plan endpoint."
}

if ($Styles -notmatch "Local video composer") {
    throw "Global styles missing local video composer marker."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-8 Completed",
    r'''
## Release Pack AI-8 Completed

Name:

Campaign-to-Variants Planner + Local Video Tool Foundation

Added files:

- backend/src/services/local_video_service.py
- backend/tests/smoke_test_local_video.py
- frontend/src/components/plan-campaign-variants-action.tsx
- frontend/src/components/create-local-video-job-form.tsx
- frontend/src/components/run-local-video-job-action.tsx
- frontend/src/app/produce/video/page.tsx
- frontend/src/app/produce/video/[jobId]/page.tsx

Updated files:

- backend/src/api/publishing.py
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- frontend/src/app/produce/page.tsx
- frontend/src/app/publishing/campaigns/[campaignId]/page.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- campaign detail can generate platform-specific variants through existing variants planner
- local video jobs can be created from start image, optional end image and prompt
- default video duration is 4 seconds
- duration, aspect ratio and FPS are configurable
- local video dry-run prepares input JSON
- real local execution is adapter-based through DAMA_LOCAL_VIDEO_COMMAND

Required for real local video generation later:

- set DAMA_LOCAL_VIDEO_COMMAND to a local executable/script
- that command receives input_json_path and output_video_path as arguments
- examples can be built for ComfyUI, Wan, AnimateDiff or other local tools
    ''',
)


print("Release Pack AI-8 applied successfully.")
