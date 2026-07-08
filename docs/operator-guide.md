# DAMA Operator Guide

This guide explains how to run, check, and maintain DAMA locally.

## Local Backend

Run the backend:

    cd I:\DAMA\backend
    .\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

Open Swagger:

    http://127.0.0.1:8000/docs

Open OpenAPI JSON:

    http://127.0.0.1:8000/openapi.json

## Backend Check

Run all backend smoke tests:

    cd I:\DAMA
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-check.ps1

## Core Operational Endpoints

    GET /api
    GET /dashboard/summary
    GET /maintenance/status
    GET /system/status
    GET /developer/endpoint-map
    GET /developer/frontend-contract
    GET /developer/runbook

## Safe Working Order

1. Create a project.
2. Create draft assets or generate project content.
3. Review project summary.
4. Export content asset or project bundle.
5. Run database backup.
6. Commit and push stable changes.

## Backup

Create local database backup:

    POST /maintenance/database/backup

Backup directory:

    backend/backups

The backup directory is ignored by Git.
