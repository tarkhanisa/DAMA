from pathlib import Path

root = Path("I:/DAMA")
gitignore = root / ".gitignore"

text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""

lines = [
    "",
    "# DAMA runtime data - never commit",
    "backend/data/",
    "backend/data/**",
    "backend/exports/",
    "backend/exports/**",
    "backend/backups/",
    "backend/backups/**",
]

for line in lines:
    if line and line not in text:
        text += "\n" + line

gitignore.write_text(text.strip() + "\n", encoding="utf-8")

print(".gitignore hardened for backend runtime data.")
