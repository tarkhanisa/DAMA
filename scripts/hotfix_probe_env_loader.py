from pathlib import Path

ROOT = Path("I:/DAMA")

probe = ROOT / "scripts/probe_local_ai_tools.py"

probe.write_text(
    r'''
from __future__ import annotations

from pathlib import Path
import json
import os
import sys


ROOT = Path("I:/DAMA")
BACKEND = ROOT / "backend"
ENV_PATH = BACKEND / ".env.local"

sys.path.insert(0, str(BACKEND))


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(ENV_PATH)

from src.services.local_ai_tools_service import local_ai_tools_status  # noqa: E402


def main() -> None:
    print(json.dumps(local_ai_tools_status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
    ''',
    encoding="utf-8",
)

print("probe_local_ai_tools.py patched.")
