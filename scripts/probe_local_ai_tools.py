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
