# DAMA Security Baseline

DAMA now has a local security baseline for development.

## Current Safety Defaults

- Runtime database files are ignored.
- Export files are ignored.
- Backup files are ignored.
- Frontend build caches are ignored.
- Frontend dependencies are pinned away from floating latest versions.
- Frontend has a package-lock file.
- Backend has CORS configured only for local frontend development origins.
- Destructive UI operations are intentionally not exposed.
- Operations UI uses confirmation-first actions.

## Local Security Checks

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security-baseline-check.ps1

This checks:

- required .gitignore entries
- pinned frontend dependencies
- CORS presence
- tracked runtime/cache files

## Dependency Audit

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

This creates snapshots in:

    docs/dependency-snapshots/

## Policy

Do not run:

    npm audit fix --force

without reviewing the breaking changes first.

## Configuration Safety

Release Pack S adds a configuration baseline.

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\config-baseline-check.ps1

This verifies:

- safe `.env.example`
- real env files are not tracked
- frontend uses `NEXT_PUBLIC_DAMA_API_BASE_URL`
- backend CORS baseline exists
