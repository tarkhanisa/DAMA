# DAMA Dashboard UI

Super Pack I adds the first real dashboard UI.

## Current Data Source

The dashboard page fetches:

    GET /dashboard/summary
    GET /developer/frontend-contract

## Current UI Sections

- Hero status
- Project count
- Content asset count
- Markdown export count
- Workflow readiness
- System readiness panel
- Project breakdowns
- Content asset breakdowns
- Recent projects
- Recent content assets
- Developer quick links

## Backend Requirement

Start backend first:

    cd I:\DAMA\backend
    .\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

## Frontend Requirement

Install dependencies:

    cd I:\DAMA\frontend
    npm install

Run frontend:

    npm run dev

## Notes

The dashboard page is resilient. If the backend is unavailable, it shows a backend unavailable state instead of crashing.
