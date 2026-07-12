from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import shutil


ROOT = Path("I:/DAMA")
DATA_DIR = ROOT / "backend/data"
BACKUP_ROOT = ROOT / "backend/backups/runtime-cleanup"


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def backup_data() -> Path:
    backup_dir = BACKUP_ROOT / now_slug()
    backup_dir.mkdir(parents=True, exist_ok=True)

    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            target = backup_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    return backup_dir


def create_clean_channels() -> list[dict[str, object]]:
    now = datetime.now(timezone.utc).isoformat()

    return [
        {
            "id": str(uuid4()),
            "name": "وردپرس لوکال دامامدیا",
            "channel_type": "wordpress",
            "target_url": "http://damamedia.local",
            "status": "active",
            "notes": "کانال تمیز برای ساخت Draft در وردپرس لوکال دامامدیا.",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid4()),
            "name": "تلگرام تست دامامدیا",
            "channel_type": "telegram",
            "target_url": "",
            "status": "active",
            "notes": "کانال تمیز برای تست Bot تلگرام. chat_id از env یا فرم گرفته می‌شود.",
            "created_at": now,
            "updated_at": now,
        },
    ]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_data()

    write_json(DATA_DIR / "publishing_channels.json", create_clean_channels())
    write_json(DATA_DIR / "publishing_variants.json", [])
    write_json(DATA_DIR / "publishing_attempts.json", [])
    write_json(DATA_DIR / "publishing_queue.json", [])

    print("Runtime data cleanup completed.")
    print(f"Backup created at: {backup_dir}")
    print("Clean channels recreated:")
    print("- وردپرس لوکال دامامدیا")
    print("- تلگرام تست دامامدیا")


if __name__ == "__main__":
    main()
