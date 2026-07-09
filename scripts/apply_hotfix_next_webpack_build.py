from pathlib import Path
import json

ROOT = Path("I:/DAMA")

package_path = ROOT / "frontend/package.json"
package_data = json.loads(package_path.read_text(encoding="utf-8"))

package_data["scripts"]["dev"] = "next dev --webpack"
package_data["scripts"]["build"] = "next build --webpack"
package_data["scripts"]["typecheck"] = "tsc --noEmit"
package_data["scripts"]["check"] = "npm run typecheck"

package_path.write_text(
    json.dumps(package_data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

# Keep Next's mandatory TypeScript update: jsx react-jsx and .next/dev types.
tsconfig_path = ROOT / "frontend/tsconfig.json"
tsconfig = json.loads(tsconfig_path.read_text(encoding="utf-8"))

tsconfig.setdefault("compilerOptions", {})
tsconfig["compilerOptions"]["jsx"] = "react-jsx"

include = tsconfig.get("include", [])
for item in [
    "next-env.d.ts",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.ts",
    "**/*.tsx",
]:
    if item not in include:
        include.append(item)

tsconfig["include"] = include

tsconfig_path.write_text(
    json.dumps(tsconfig, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

# Use npm.cmd in frontend-check too if node_modules exists.
frontend_check = ROOT / "scripts/frontend-check.ps1"
text = frontend_check.read_text(encoding="utf-8")
text = text.replace("npm run typecheck", "npm.cmd run typecheck")
frontend_check.write_text(text, encoding="utf-8")

# Document this stabilization.
doc_path = ROOT / "docs/frontend-build-hardening.md"
doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
marker = "## Webpack Build Stabilization"
if marker not in doc:
    doc += """

## Webpack Build Stabilization

Next.js 16 uses Turbopack by default. Release Pack P stabilizes local builds by using:

    next dev --webpack
    next build --webpack

This avoids unclear Turbopack build-worker failures on the local Windows setup.
"""
doc_path.write_text(doc.strip() + "\n", encoding="utf-8")

status_path = ROOT / "docs/project-status.md"
status = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
marker = "## Frontend Webpack Build Hotfix"
if marker not in status:
    status += """

## Frontend Webpack Build Hotfix

The frontend build script was stabilized by switching Next.js build/dev commands to Webpack:

- next dev --webpack
- next build --webpack

Reason:

Next.js 16.2 local Turbopack build failed with an unclear build worker error.
"""
status_path.write_text(status.strip() + "\n", encoding="utf-8")

print("Next frontend build switched to Webpack mode.")
