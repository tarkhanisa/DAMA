from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter


router = APIRouter(prefix="/runtime", tags=["runtime"])

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status_value(ok: bool, warning: bool = False) -> str:
    if ok:
        return "ok"
    if warning:
        return "warning"
    return "error"


def path_probe(label: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    is_directory = path.is_dir() if exists else False
    check_target = path if exists else path.parent
    writable = os.access(check_target, os.W_OK) if check_target.exists() else False

    return {
        "label": label,
        "path": str(path),
        "exists": exists,
        "is_directory": is_directory,
        "writable": writable,
        "status": status_value(exists and is_directory and writable, warning=True),
    }


def tcp_probe(host: str, port: int, timeout_seconds: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def ollama_probe() -> dict[str, Any]:
    base_url = os.getenv("DAMA_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    tags_url = f"{base_url}/api/tags"

    try:
        request = Request(tags_url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=1.0) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            models = payload.get("models", [])

        return {
            "status": "ok",
            "base_url": base_url,
            "reachable": True,
            "model_count": len(models),
            "models": [
                model.get("name")
                for model in models
                if isinstance(model, dict) and model.get("name")
            ][:20],
        }
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "status": "warning",
            "base_url": base_url,
            "reachable": False,
            "model_count": 0,
            "models": [],
            "message": str(exc),
        }


def safe_config() -> dict[str, Any]:
    public_keys = [
        "DAMA_ENV",
        "DAMA_DEBUG",
        "DAMA_API_BASE_URL",
        "DAMA_FRONTEND_ORIGIN",
        "DAMA_AI_PROVIDER",
        "DAMA_OLLAMA_BASE_URL",
        "DAMA_OLLAMA_DEFAULT_MODEL",
    ]

    return {
        "environment": {
            key: os.getenv(key)
            for key in public_keys
            if os.getenv(key) is not None
        },
        "has_next_public_api_url": os.getenv("NEXT_PUBLIC_DAMA_API_BASE_URL") is not None,
        "secrets_redacted": True,
    }


@router.get("/health")
def runtime_health() -> dict[str, Any]:
    data_dir = Path(os.getenv("DAMA_DATA_DIR", str(BACKEND_ROOT / "data")))
    exports_dir = Path(os.getenv("DAMA_EXPORTS_DIR", str(BACKEND_ROOT / "exports")))
    backups_dir = Path(os.getenv("DAMA_BACKUPS_DIR", str(BACKEND_ROOT / "backups")))

    storage = [
        path_probe("data", data_dir),
        path_probe("exports", exports_dir),
        path_probe("backups", backups_dir),
    ]

    storage_required_ok = all(item["exists"] and item["is_directory"] for item in storage)
    storage_writable = all(item["writable"] for item in storage)

    ollama = ollama_probe()

    overall = "ok"
    if not storage_required_ok:
        overall = "warning"
    if storage_required_ok and not storage_writable:
        overall = "warning"

    return {
        "ok": overall == "ok",
        "status": overall,
        "checked_at": utc_now(),
        "backend": {
            "status": "ok",
            "project_root": str(PROJECT_ROOT),
            "backend_root": str(BACKEND_ROOT),
            "runtime": "fastapi",
        },
        "storage": storage,
        "ollama": ollama,
        "config": safe_config(),
        "operator_notes": [
            "Ollama unreachable is warning-level for UI readiness, not a backend failure.",
            "Runtime paths should exist before real production deployment.",
            "Secrets are intentionally not returned by this endpoint.",
        ],
    }
