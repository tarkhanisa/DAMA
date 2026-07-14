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
