from pathlib import Path
import re

target = Path("I:/DAMA/backend/src/main.py")
text = target.read_text(encoding="utf-8")

# Remove broken imports.
text = text.replace(
    "from fastapi.middleware.cors import CORSMiddleware, HTTPException, Request\n",
    ""
)
text = text.replace(
    "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware, HTTPException, Request\n",
    ""
)

# Remove duplicate partial imports if any.
text = re.sub(r"from fastapi import .*\n", "", text, count=1)
text = re.sub(r"from fastapi\.middleware\.cors import .*\n", "", text, count=1)

# Add clean imports at the top after future import if present.
lines = text.splitlines()
insert_at = 0

if lines and lines[0].startswith("from __future__"):
    insert_at = 1

clean_imports = [
    "from fastapi import FastAPI, HTTPException, Request",
    "from fastapi.middleware.cors import CORSMiddleware",
]

for item in reversed(clean_imports):
    lines.insert(insert_at, item)

text = "\n".join(lines).strip() + "\n"

if "from fastapi.middleware.cors import CORSMiddleware, HTTPException, Request" in text:
    raise RuntimeError("Broken CORS import still exists.")

if "from fastapi import FastAPI, HTTPException, Request" not in text:
    raise RuntimeError("Clean FastAPI import missing.")

if "from fastapi.middleware.cors import CORSMiddleware" not in text:
    raise RuntimeError("Clean CORS import missing.")

target.write_text(text, encoding="utf-8")

print("backend/src/main.py FastAPI/CORS imports fixed.")
