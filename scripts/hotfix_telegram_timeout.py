from pathlib import Path

ROOT = Path("I:/DAMA")
target = ROOT / "backend/src/services/telegram_connector_service.py"

text = target.read_text(encoding="utf-8")

text = text.replace(
    "with urlopen(request, timeout=45) as response:",
    "with urlopen(request, timeout=float(os.getenv(\"DAMA_TELEGRAM_TIMEOUT_SECONDS\", \"8\"))) as response:"
)

target.write_text(text, encoding="utf-8")

print("Telegram connector timeout reduced and made configurable.")
