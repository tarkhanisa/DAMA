from __future__ import annotations

from pathlib import Path
import os


BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent

DEFAULT_ENV_PATHS = [
    REPO_ROOT / ".env.local",
    REPO_ROOT / ".env",
    BACKEND_ROOT / ".env.local",
    BACKEND_ROOT / ".env",
]


def strip_quotes(value: str) -> str:
    value = value.strip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value


def parse_env_line(line: str) -> tuple[str, str] | None:
    cleaned = line.strip()

    if not cleaned or cleaned.startswith("#"):
        return None

    if cleaned.startswith("export "):
        cleaned = cleaned[len("export "):].strip()

    if "=" not in cleaned:
        return None

    key, value = cleaned.split("=", 1)
    key = key.strip()
    value = strip_quotes(value)

    if not key:
        return None

    return key, value


def load_env_file(path: Path, override: bool = False) -> dict[str, str]:
    loaded: dict[str, str] = {}

    if not path.exists():
        return loaded

    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(line)

        if not parsed:
            continue

        key, value = parsed

        if override or key not in os.environ:
            os.environ[key] = value
            loaded[key] = value

    return loaded


def load_local_env(override: bool = False) -> dict[str, str]:
    loaded: dict[str, str] = {}

    for path in DEFAULT_ENV_PATHS:
        loaded.update(load_env_file(path, override=override))

    return loaded
