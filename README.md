# DAMA

DAMA is an AI Content Automation Platform.

The goal of DAMA is to become a production-grade AI operating platform for content creation, prompt management, local LLM integration, content generation, publishing workflows, scheduling, agents, dashboards, and plugin-based automation.

## Current Backend Status

The backend is built with FastAPI and currently supports:

- API index
- Local Ollama model discovery
- Raw text generation
- Prompt-template based generation
- Structured content generation
- Standard content type catalog
- AI provider catalog
- System status endpoint
- Fast backend smoke test

## Tech Stack

- FastAPI
- Ollama
- PostgreSQL
- Redis
- Celery
- Next.js
- Docker

## Repository Structure

- backend/
- frontend/
- workers/
- docs/
- scripts/

## Backend

Backend source:

backend/src/

Current service layer:

- ollama_service.py
- ai_service.py
- prompt_service.py
- content_service.py
- system_service.py

Current API layer:

backend/src/api/

## Local Development

Go to the backend folder:

cd I:\DAMA\backend

Run the backend locally:

.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

Open Swagger UI:

http://127.0.0.1:8000/docs

## Fast Backend Check

Run the backend smoke test:

cd I:\DAMA
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-check.ps1

## Current API Endpoints

GET  /
GET  /api
GET  /models
POST /generate
GET  /content/types
GET  /content/types/{key}
POST /content/generate
GET  /providers
GET  /providers/{key}
GET  /system/status

## API Documentation

Backend API documentation:

docs/backend-api.md

## Current Local Model

qwen2.5-coder:7b

## Development Workflow

Local Development
Testing
Code Review
Commit
Push

## Development Rules

- One task at a time
- Prefer one file per step when possible
- Test before commit
- Commit after each stable step
- Do not add mock or fake outputs
- Use real services and real system calls

## Roadmap

Phase 1:

- FastAPI backend
- Ollama integration
- Prompt engine
- Content generator

Phase 2:

- Image generation
- Publisher
- Scheduler
- Dashboard

Phase 3:

- Memory
- RAG
- Agents
- Plugin system

## DAMA Autopilot

Check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 check

Status:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 status

Ship:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"

Backup:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 backup

## DAMA Local Development

Start backend:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1

Start frontend:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1

Start both in separate PowerShell windows:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-all.ps1

Backend:

    http://127.0.0.1:8000

Frontend:

    http://localhost:3000

API Docs:

    http://127.0.0.1:8000/docs

Run full ship checks and commit/push:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Your commit message"

## DAMA Security and Dependency Checks

Run repo hygiene check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\repo-hygiene-check.ps1

Run security baseline check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security-baseline-check.ps1

Run dependency audit snapshot:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dependency-audit.ps1

Do not run npm audit fix --force without review.

## DAMA Configuration

Configuration example:

    .env.example

Copy locally if needed:

    Copy-Item .\.env.example .\.env

Run config baseline check:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\config-baseline-check.ps1

Create backend dependency snapshot:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-requirements-snapshot.ps1

## DAMA Runtime Health

Backend runtime health:

    http://127.0.0.1:8000/runtime/health

Frontend runtime dashboard:

    http://localhost:3000/runtime

This dashboard is read-only and safe for operator diagnostics.
