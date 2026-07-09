# DAMA Environment Checklist

## Local Backend

Required:

- Python virtual environment exists at `backend/.venv`
- FastAPI app imports successfully
- Uvicorn can run `src.main:app`
- Backend opens on `http://127.0.0.1:8000`

Command:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1

## Local Frontend

Required:

- Node.js installed
- npm.cmd available
- frontend/package-lock.json committed
- frontend/node_modules installed locally
- frontend builds successfully

Command:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1

## Local Ollama

Required:

- Ollama installed
- Ollama service running
- Model available locally

Recommended model:

    qwen2.5-coder:7b

## Checks

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check

Before shipping:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"

## Do Not Commit

- `.env`
- database files
- export files
- backup files
- frontend build output
- dependency folders
