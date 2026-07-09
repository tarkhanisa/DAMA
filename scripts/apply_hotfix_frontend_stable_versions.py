from pathlib import Path
import json
import shutil

ROOT = Path("I:/DAMA")
FRONTEND = ROOT / "frontend"

package_path = FRONTEND / "package.json"

package_data = {
    "name": "dama-frontend",
    "version": "0.1.0",
    "private": True,
    "description": "Frontend foundation for DAMA AI Content Automation Platform.",
    "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start",
        "typecheck": "tsc --noEmit",
        "check": "npm.cmd run typecheck"
    },
    "dependencies": {
        "next": "15",
        "react": "19",
        "react-dom": "19"
    },
    "devDependencies": {
        "@types/node": "^22.0.0",
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
        "typescript": "^5.6.0"
    }
}

package_path.write_text(
    json.dumps(package_data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

tsconfig_path = FRONTEND / "tsconfig.json"
tsconfig_data = {
    "compilerOptions": {
        "target": "ES2017",
        "lib": ["dom", "dom.iterable", "esnext"],
        "allowJs": False,
        "skipLibCheck": True,
        "strict": True,
        "noEmit": True,
        "esModuleInterop": True,
        "module": "esnext",
        "moduleResolution": "bundler",
        "resolveJsonModule": True,
        "isolatedModules": True,
        "jsx": "preserve",
        "incremental": True,
        "types": ["node", "react", "react-dom"],
        "plugins": [{"name": "next"}]
    },
    "include": [
        "next-env.d.ts",
        ".next/types/**/*.ts",
        ".next/dev/types/**/*.ts",
        "**/*.ts",
        "**/*.tsx"
    ],
    "exclude": ["node_modules"]
}

tsconfig_path.write_text(
    json.dumps(tsconfig_data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

next_env = FRONTEND / "next-env.d.ts"
next_env.write_text(
    """/// <reference types="next" />
/// <reference types="next/image-types/global" />

// This file is required by Next.js TypeScript projects.
""",
    encoding="utf-8",
)

for folder in [FRONTEND / ".next", FRONTEND / "node_modules"]:
    if folder.exists():
        shutil.rmtree(folder)
        print(f"Removed {folder}")

lock_file = FRONTEND / "package-lock.json"
if lock_file.exists():
    lock_file.unlink()
    print("Removed package-lock.json")

doc_path = ROOT / "docs/frontend-build-hardening.md"
doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
marker = "## Stable Frontend Version Pin"
if marker not in doc:
    doc += """

## Stable Frontend Version Pin

The frontend dependencies were pinned away from floating latest versions.

Current stabilized frontend line:

- next: 15
- react: 19
- react-dom: 19
- typescript: ^5.6.0

Reason:

The local Windows build with Next latest / Next 16 produced an unclear build-worker failure. The project now prioritizes stable reproducible builds over newest-version adoption.
"""
doc_path.write_text(doc.strip() + "\n", encoding="utf-8")

status_path = ROOT / "docs/project-status.md"
status = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
marker = "## Frontend Stable Version Pin"
if marker not in status:
    status += """

## Frontend Stable Version Pin

Frontend dependencies were stabilized by replacing floating latest versions with a Next 15 line.

Reason:

Next latest / Next 16 produced an unclear local build-worker failure on Windows.

Goal:

Make frontend install, typecheck, and build reproducible before adding more UI features.
"""
status_path.write_text(status.strip() + "\n", encoding="utf-8")

print("Frontend dependencies pinned and build cache cleaned.")
