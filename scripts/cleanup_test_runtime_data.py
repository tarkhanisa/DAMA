from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT = Path("I:/DAMA")
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from src.services.runtime_cleanup_service import cleanup_test_runtime_data  # noqa: E402


def main() -> None:
    preview = cleanup_test_runtime_data(dry_run=True)
    print("Preview:")
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    if preview["totals"]["removed"] == 0:
        print("No test runtime data found.")
        return

    result = cleanup_test_runtime_data(dry_run=False, backup=True)
    print("\nCleanup completed:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
