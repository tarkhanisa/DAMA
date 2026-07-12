from __future__ import annotations

from pathlib import Path
import re


ROOT = Path("I:/DAMA")
FRONTEND_SRC = ROOT / "frontend/src"
REPORT_PATH = ROOT / "docs/frontend-copy-audit.md"

SUSPICIOUS_TERMS = [
    "Dry-run",
    "dry-run",
    "Queue",
    "Attempt",
    "Connector",
    "Mode",
    "Run",
    "Test Send",
    "Ready",
    "Draft",
    "Publish",
    "WordPress",
    "Telegram",
    "unknown error",
    "Failed to fetch",
]

SKIP_FILES = {
    "frontend/src/lib/persian-copy.ts",
}

SKIP_PARTS = {
    ".next",
    "node_modules",
}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()

    if rel in SKIP_FILES:
        return True

    return any(part in path.parts for part in SKIP_PARTS)


def main() -> None:
    findings: list[str] = []

    for path in sorted(FRONTEND_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue

        if should_skip(path):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        for index, line in enumerate(lines, start=1):
            for term in SUSPICIOUS_TERMS:
                if term in line:
                    clean = re.sub(r"\s+", " ", line).strip()
                    rel = path.relative_to(ROOT).as_posix()
                    findings.append(f"- `{rel}:{index}` — `{term}` — `{clean}`")
                    break

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if findings:
        body = "\n".join(findings[:300])
        if len(findings) > 300:
            body += f"\n\n... and {len(findings) - 300} more findings.\n"
    else:
        body = "No obvious English UI copy terms were found."

    REPORT_PATH.write_text(
        "# Frontend Persian Copy Audit\n\n"
        "This report lists suspicious English UI terms that may still need Persian wording.\n\n"
        f"Total findings: {len(findings)}\n\n"
        f"{body}\n",
        encoding="utf-8",
    )

    print(f"Frontend copy audit completed. Findings: {len(findings)}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
