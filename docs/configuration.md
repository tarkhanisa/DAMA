# DAMA Configuration

DAMA uses a local-first configuration baseline.

## Environment Example

The repository includes:

    .env.example

Copy it locally when needed:

    Copy-Item .\.env.example .\.env

Do not commit real `.env` files.

## Main Local Values

Backend URL:

    http://127.0.0.1:8000

Frontend URL:

    http://localhost:3000

Ollama URL:

    http://127.0.0.1:11434

Default local model:

    qwen2.5-coder:7b

## Frontend API Base URL

Frontend reads:

    NEXT_PUBLIC_DAMA_API_BASE_URL

Default:

    http://127.0.0.1:8000

## Backend CORS

Backend currently allows local frontend origins:

    http://localhost:3000
    http://127.0.0.1:3000
    http://localhost:3001
    http://127.0.0.1:3001

## Config Check

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\config-baseline-check.ps1

## Rule

Real secrets must not be committed.

Use `.env.example` only for safe defaults and documentation.
