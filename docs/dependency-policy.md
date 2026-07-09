# DAMA Dependency Policy

## Core Rule

DAMA prioritizes reproducible local builds over newest possible package versions.

## Frontend

Frontend packages should not use floating `latest`.

Current policy:

- Keep Next.js pinned to a stable major line.
- Keep React pinned to a stable major line.
- Commit package-lock.json.
- Do not run npm audit fix --force without review.

## Backend

Backend dependencies are managed through:

    backend/requirements.txt

A local freeze snapshot can be generated through:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

Snapshot output:

    docs/dependency-snapshots/backend-pip-freeze.txt

## Vulnerability Handling

Recommended order:

1. Record audit result.
2. Identify affected package.
3. Check whether the package is direct or transitive.
4. Prefer non-breaking patch/minor upgrades.
5. Avoid force upgrades unless the project can be tested immediately.
6. Run full DAMA ship check after dependency changes.

## Current npm Audit Note

If npm reports moderate vulnerabilities, document them first.

Do not use `npm audit fix --force` as an automatic step.
