from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import shutil
import subprocess


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_DIR = BACKEND_ROOT / "data"
SESSION_PATH = DATA_DIR / "operator_session.json"
BACKUP_ROOT = BACKEND_ROOT / "backups" / "safe-exit"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_session_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SESSION_PATH.exists():
        SESSION_PATH.write_text(
            json.dumps(
                {
                    "last_route": "/",
                    "updated_at": utc_now(),
                    "history": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def read_operator_session() -> dict[str, Any]:
    ensure_session_store()

    try:
        payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {}

    return payload if isinstance(payload, dict) else {}


def write_operator_session(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_session_store()
    payload["updated_at"] = utc_now()

    SESSION_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def normalize_route(route: Any) -> str:
    text = str(route or "/").strip()

    if not text.startswith("/"):
        text = "/" + text

    if text in {"/other/exit", "/exit"}:
        return "/"

    return text


def update_last_route(route: Any) -> dict[str, Any]:
    session = read_operator_session()
    next_route = normalize_route(route)

    session["last_route"] = next_route
    session["last_route_updated_at"] = utc_now()

    history = session.get("history")
    if not isinstance(history, list):
        history = []

    history.insert(
        0,
        {
            "event": "route_updated",
            "route": next_route,
            "at": utc_now(),
        },
    )

    session["history"] = history[:100]

    return write_operator_session(session)


def backup_runtime_data() -> str:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup_dir = BACKUP_ROOT / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            target = backup_dir / item.name

            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    return str(backup_dir)


def schedule_dama_shutdown(delay_seconds: int = 2) -> None:
    script_path = PROJECT_ROOT / "scripts" / "dama-stop.ps1"

    if not script_path.exists():
        return

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-DelaySeconds",
        str(max(0, delay_seconds)),
        "-SkipBackup",
    ]

    creationflags = 0

    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def safe_exit(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = payload or {}
    last_route = normalize_route(request.get("last_route") or "/")
    make_backup = bool(request.get("backup", True))
    shutdown = bool(request.get("shutdown", True))

    session = update_last_route(last_route)

    backup_path = ""

    if make_backup:
        backup_path = backup_runtime_data()

    session["last_safe_exit_at"] = utc_now()
    session["last_safe_exit_route"] = last_route
    session["last_safe_exit_backup_path"] = backup_path
    session = write_operator_session(session)

    if shutdown:
        schedule_dama_shutdown(delay_seconds=2)

    return {
        "ok": True,
        "last_route": last_route,
        "backup_path": backup_path,
        "shutdown_scheduled": shutdown,
        "message": (
            "خروج امن ثبت شد. تا چند ثانیه دیگر سرورهای DAMA بسته می‌شوند."
            if shutdown
            else "خروج امن ثبت شد."
        ),
        "session": session,
    }
