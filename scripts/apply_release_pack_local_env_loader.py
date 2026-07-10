from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


def patch_main() -> None:
    target = ROOT / "backend/src/main.py"
    text = target.read_text(encoding="utf-8")

    if "load_local_env()" in text:
        print("Skipped backend/src/main.py env loader patch.")
        return

    insert = "from src.core.env_loader import load_local_env\n\nload_local_env()\n\n"

    if text.startswith("from __future__ import annotations\n"):
        text = text.replace(
            "from __future__ import annotations\n",
            "from __future__ import annotations\n\n" + insert,
            1,
        )
    else:
        text = insert + text

    target.write_text(text, encoding="utf-8")
    print("Patched backend/src/main.py")


def patch_backend_check() -> None:
    target = ROOT / "scripts/backend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "smoke_test_local_env_loader.py" in text:
        print("Skipped backend-check patch.")
        return

    text = text.rstrip() + r'''

$LocalEnvLoaderSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_local_env_loader.py"
$LocalEnvLoaderPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $LocalEnvLoaderSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_local_env_loader.py..."
    & $LocalEnvLoaderPython $LocalEnvLoaderSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_local_env_loader.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


write_file(
    "backend/src/core/__init__.py",
    r'''
    ''',
)


write_file(
    "backend/src/core/env_loader.py",
    r'''
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
    ''',
)


write_file(
    "backend/tests/smoke_test_local_env_loader.py",
    r'''
from pathlib import Path
import os
import tempfile

from src.core.env_loader import load_env_file, parse_env_line


def main() -> None:
    assert parse_env_line("DAMA_TEST_KEY=value") == ("DAMA_TEST_KEY", "value")
    assert parse_env_line("export DAMA_TEST_KEY='quoted value'") == (
        "DAMA_TEST_KEY",
        "quoted value",
    )
    assert parse_env_line("# comment") is None

    key = "DAMA_LOCAL_ENV_LOADER_SMOKE"
    os.environ.pop(key, None)

    with tempfile.TemporaryDirectory() as directory:
        env_path = Path(directory) / ".env.local"
        env_path.write_text(
            f"""
# smoke env
{key}=loaded-from-file
DAMA_QUOTED_VALUE="hello world"
""".strip()
            + "\n",
            encoding="utf-8",
        )

        loaded = load_env_file(env_path)

    assert loaded[key] == "loaded-from-file"
    assert os.getenv(key) == "loaded-from-file"
    assert os.getenv("DAMA_QUOTED_VALUE") == "hello world"

    print("Local env loader smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "backend/.env.local.example",
    r'''
# DAMA backend local environment
# Copy this file to:
# backend/.env.local
#
# Never commit backend/.env.local

# WordPress Draft Connector
DAMA_WORDPRESS_BASE_URL=https://your-wordpress-site.com
DAMA_WORDPRESS_USERNAME=your-wordpress-username
DAMA_WORDPRESS_APP_PASSWORD=your-wordpress-application-password

# Keep disabled unless you have confirmed SEO meta fields are supported by your WordPress REST setup.
DAMA_WORDPRESS_SEND_SEO_META=false

# Ollama
DAMA_OLLAMA_BASE_URL=http://127.0.0.1:11434
DAMA_OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b
    ''',
)


append_once(
    ".gitignore",
    "# DAMA local env files",
    r'''
# DAMA local env files
.env
.env.local
backend/.env
backend/.env.local
frontend/.env
frontend/.env.local

# Keep examples
!.env.example
!backend/.env.local.example
!frontend/.env.example
    ''',
)


append_once(
    ".env.example",
    "backend/.env.local",
    r'''
# Backend local env loader
# Backend also reads:
# backend/.env.local
# backend/.env
# .env.local
# .env
    ''',
)


write_file(
    "docs/real-wordpress-draft-test.md",
    r'''
# Real WordPress Draft Test Setup

This checklist is for creating the first real WordPress draft from DAMA.

DAMA still does not publish posts directly.

It only creates WordPress posts with:

    status = draft

## 1. Create WordPress Application Password

In WordPress admin:

1. Go to Users.
2. Open the user profile that DAMA should use.
3. Find Application Passwords.
4. Add a new application password named:

       DAMA Local Draft Connector

5. Copy the generated password once.

Do not paste this password into ChatGPT.

## 2. Create backend/.env.local

Copy:

    backend/.env.local.example

to:

    backend/.env.local

Fill:

    DAMA_WORDPRESS_BASE_URL=https://your-wordpress-site.com
    DAMA_WORDPRESS_USERNAME=your-wordpress-username
    DAMA_WORDPRESS_APP_PASSWORD=your-application-password

## 3. Restart backend

After changing backend/.env.local, restart the backend server.

## 4. Test WordPress status page

Open:

    http://localhost:3000/publishing/wordpress

Run:

1. Dry-run test
2. Real WordPress test

The real test should authenticate with:

    /wp-json/wp/v2/users/me

## 5. Create one real draft

Use a WordPress variant that is:

    ready_for_publish

Then create a WordPress draft with mode:

    wordpress

Check:

    /publishing/attempts

Then open the attempt detail page.

## 6. Safety rules

- Do not commit backend/.env.local.
- Do not use your main admin account if a dedicated editor user can be used.
- Do not enable direct publish yet.
- Do not enable SEO meta sending unless the target site supports it.
    ''',
)


append_once(
    "docs/configuration.md",
    "## Local Env Loader",
    r'''
## Local Env Loader

Backend now loads local env files automatically.

Load order:

    .env.local
    .env
    backend/.env.local
    backend/.env

Existing system environment variables are not overwritten.

Recommended file for local development:

    backend/.env.local

Never commit real secrets.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AD Completed",
    r'''
## Release Pack AD Completed

Name:

Backend Local Env Loader + Real WordPress Test Checklist

Added files:

- backend/src/core/__init__.py
- backend/src/core/env_loader.py
- backend/tests/smoke_test_local_env_loader.py
- backend/.env.local.example
- docs/real-wordpress-draft-test.md

Updated files:

- backend/src/main.py
- scripts/backend-check.ps1
- .gitignore
- .env.example
- docs/configuration.md
- docs/project-status.md

Added behavior:

- backend loads local env files automatically
- WordPress credentials can be stored locally in backend/.env.local
- local env files are ignored by git
- smoke test validates env loading
- real WordPress draft checklist added

Next recommended Release Pack:

Release Pack AE: Real WordPress Draft Test Run

Suggested scope:

- choose target WordPress site
- create Application Password
- configure backend/.env.local
- test /publishing/wordpress
- create one real WordPress draft
- no direct publish yet
    ''',
)


patch_main()
patch_backend_check()

print("Release Pack AD applied successfully.")
