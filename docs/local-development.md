# DAMA Local Development

## Backend

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1

Backend URL:

    http://127.0.0.1:8000

API Docs:

    http://127.0.0.1:8000/docs

## Frontend

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1

Frontend URL:

    http://localhost:3000

## Start Both

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-all.ps1

This opens backend and frontend in separate PowerShell windows.

## Real Frontend Build

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\frontend-real-build.ps1

## Ship

Run:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama.ps1 ship "Commit message"
