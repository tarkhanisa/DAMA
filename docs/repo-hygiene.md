# DAMA Repository Hygiene

## Tracked

- Source code
- Documentation
- Frontend package lock
- Smoke tests
- Operator scripts

## Ignored

- backend/data
- backend/exports
- backend/backups
- frontend/node_modules
- frontend/.next
- frontend/out
- frontend/tsconfig.tsbuildinfo
- frontend/*.tsbuildinfo

## Check

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\repo-hygiene-check.ps1

## Note

Generated runtime files should remain local and should not be committed.
