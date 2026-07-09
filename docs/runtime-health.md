# DAMA Runtime Health

Release Pack T adds a read-only runtime health endpoint and frontend page.

## Backend Endpoint

    GET /runtime/health

Returns:

- backend runtime status
- local storage path status
- Ollama reachability
- safe public config
- operator notes

## Frontend Page

    http://localhost:3000/runtime

## Safety

This endpoint is read-only.

It does not:

- expose secrets
- mutate database state
- create/delete files
- run generation
- execute batch jobs

## Ollama Status

Ollama unreachable is warning-level during local development.

It means:

- backend can run
- frontend can load
- generation may fail until Ollama is started

## Smoke Test

Run:

    .\backend\.venv\Scripts\python.exe .\backend\tests\smoke_test_runtime.py

Or full check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check
