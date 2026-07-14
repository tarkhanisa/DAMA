from pathlib import Path
import os

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


def upsert_env_key(path: str, key: str, value: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)

    lines = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    next_lines = []
    found = False

    for line in lines:
        if line.strip().startswith(f"{key}="):
            next_lines.append(f"{key}={value}")
            found = True
        else:
            next_lines.append(line)

    if not found:
        next_lines.append(f"{key}={value}")

    target.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
    print(f"Updated {path}: {key}")


ffmpeg_path = os.environ.get("DAMA_SELECTED_FFMPEG_PATH", "").strip()
if not ffmpeg_path:
    raise RuntimeError("DAMA_SELECTED_FFMPEG_PATH is empty.")


write_file(
    "scripts/local_video_ffmpeg_adapter.py",
    r'''
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import shutil
import subprocess
import sys


RESOLUTIONS = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "3:4": (1080, 1440),
    "4:3": (1024, 768),
}


def load_job(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_ffmpeg() -> str:
    configured = os.getenv("DAMA_FFMPEG_PATH", "").strip()

    if configured and Path(configured).exists():
        return configured

    found = shutil.which("ffmpeg")

    if found:
        return found

    raise RuntimeError("FFmpeg پیدا نشد. DAMA_FFMPEG_PATH را روی مسیر ffmpeg.exe تنظیم کن.")


def resolve_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def run_command(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed.\n"
            f"STDOUT:\n{completed.stdout}\n\n"
            f"STDERR:\n{completed.stderr}"
        )


def make_single_image_video(
    ffmpeg: str,
    start_image: str,
    output_path: Path,
    duration: float,
    fps: int,
    width: int,
    height: int,
) -> None:
    frames = max(1, int(duration * fps))

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='min(zoom+0.0012,1.06)':d={frames}:s={width}x{height}:fps={fps},"
        "format=yuv420p"
    )

    command = [
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-i",
        start_image,
        "-t",
        str(duration),
        "-vf",
        vf,
        "-r",
        str(fps),
        "-an",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    run_command(command)


def make_two_image_video(
    ffmpeg: str,
    start_image: str,
    end_image: str,
    output_path: Path,
    duration: float,
    fps: int,
    width: int,
    height: int,
) -> None:
    transition = min(0.75, max(0.25, duration * 0.18))
    segment_duration = (duration + transition) / 2
    offset = max(0.1, segment_duration - transition)

    base_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,format=yuv420p"
    )

    filter_complex = (
        f"[0:v]{base_filter}[v0];"
        f"[1:v]{base_filter}[v1];"
        f"[v0][v1]xfade=transition=fade:duration={transition}:offset={offset},"
        f"fps={fps},format=yuv420p[v]"
    )

    command = [
        ffmpeg,
        "-y",
        "-loop",
        "1",
        "-t",
        str(segment_duration),
        "-i",
        start_image,
        "-loop",
        "1",
        "-t",
        str(segment_duration),
        "-i",
        end_image,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-t",
        str(duration),
        "-r",
        str(fps),
        "-an",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    run_command(command)


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Usage: local_video_ffmpeg_adapter.py input.json output.mp4")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    job = load_job(input_path)

    ffmpeg = require_ffmpeg()

    start_image = resolve_path(str(job.get("start_image") or ""))
    end_image = resolve_path(str(job.get("end_image") or ""))

    if not start_image or not Path(start_image).exists():
        raise RuntimeError(f"تصویر شروع پیدا نشد: {start_image}")

    if end_image and not Path(end_image).exists():
        raise RuntimeError(f"تصویر پایان پیدا نشد: {end_image}")

    duration = float(job.get("duration_seconds") or 4)
    fps = int(job.get("fps") or 24)
    aspect_ratio = str(job.get("aspect_ratio") or "16:9")
    width, height = RESOLUTIONS.get(aspect_ratio, RESOLUTIONS["16:9"])

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if end_image:
        make_two_image_video(
            ffmpeg=ffmpeg,
            start_image=start_image,
            end_image=end_image,
            output_path=output_path,
            duration=duration,
            fps=fps,
            width=width,
            height=height,
        )
    else:
        make_single_image_video(
            ffmpeg=ffmpeg,
            start_image=start_image,
            output_path=output_path,
            duration=duration,
            fps=fps,
            width=width,
            height=height,
        )

    print(f"Video created: {output_path}")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "scripts/local-video-ffmpeg-adapter.cmd",
    r'''
@echo off
set ROOT=%~dp0..
"%ROOT%\backend\.venv\Scripts\python.exe" "%ROOT%\scripts\local_video_ffmpeg_adapter.py" "%~1" "%~2"
    ''',
)


upsert_env_key("backend/.env.local", "DAMA_FFMPEG_PATH", ffmpeg_path)
upsert_env_key("backend/.env.local", "DAMA_LOCAL_VIDEO_COMMAND", "I:\\DAMA\\scripts\\local-video-ffmpeg-adapter.cmd")
upsert_env_key("backend/.env.local", "DAMA_LOCAL_VIDEO_OUTPUT_DIR", "I:\\DAMA\\backend\\outputs\\local-video")

append_once(
    ".gitignore",
    "# DAMA generated local video outputs",
    r'''
# DAMA generated local video outputs
backend/outputs/
    ''',
)

append_once(
    "docs/project-status.md",
    "## Release Pack AI-11 Completed",
    r'''
## Release Pack AI-11 Completed

Name:

FFmpeg Local Video Fallback Adapter

Added behavior:

- DAMA_FFMPEG_PATH points to the discovered ffmpeg.exe.
- DAMA_LOCAL_VIDEO_COMMAND points to the local FFmpeg adapter.
- Local video jobs can create a real MP4.
- One start image creates a short subtle-zoom video.
- Start image + end image creates a fade transition video.
- Output is saved under backend/outputs/local-video.
- This is a local fallback renderer, not AI video generation.
    ''',
)

print("Release Pack AI-11 applied successfully.")
print(f"FFmpeg path: {ffmpeg_path}")
