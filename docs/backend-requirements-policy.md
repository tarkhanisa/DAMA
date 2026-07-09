# DAMA Backend Requirements Policy

## Source of Truth

Backend dependencies should be declared in:

    backend/requirements.txt

## Snapshot

A local freeze snapshot can be generated with:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-requirements-snapshot.ps1

Output:

    docs/dependency-snapshots/backend-pip-freeze.txt

## Policy

- Do not blindly upgrade backend dependencies.
- Prefer small patch upgrades.
- Run backend smoke tests after dependency changes.
- Run full DAMA ship check before committing dependency changes.

## Future Improvement

Before production deployment, add a stronger dependency locking strategy.

Options:

- pip-tools
- uv lock
- poetry lock

For now, DAMA uses a simple requirements file plus local freeze snapshots.
