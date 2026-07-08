# DAMA Frontend Foundation

The first frontend foundation is intentionally simple.

## Current Frontend Path

    frontend/

## Current Structure

    frontend/package.json
    frontend/next.config.mjs
    frontend/tsconfig.json
    frontend/src/app/layout.tsx
    frontend/src/app/page.tsx
    frontend/src/app/globals.css
    frontend/src/lib/api-client.ts
    frontend/src/lib/types.ts

## Backend Contract

The frontend should use:

    GET /developer/frontend-contract
    GET /dashboard/summary
    GET /developer/endpoint-map
    GET /developer/runbook

## Frontend Sections

- Dashboard
- Projects
- Content Assets
- Workflows
- Exports
- Maintenance
- Developer

## Real Dashboard UI

Super Pack I upgraded the frontend from a placeholder landing page to a real dashboard UI.

Added components:

- StatCard
- ReadinessPanel
- RecentList
- CountBreakdown
- LinkCard

The page now fetches dashboard data from the backend and displays operational summaries.

## Projects and Content Assets UI

Super Pack J adds application routes for project and content asset management.

Added routes:

- /
- /projects
- /projects/[projectId]
- /content-assets

Added shared UI:

- AppNav
- DataTable
- StatusPill

## Build Hardening

Super Pack L adds TypeScript build hardening:

- TSX-safe DataTable generic syntax
- ReactNode type import
- formatter helpers
- shared error and page header components
- package typecheck script
- optional frontend typecheck when node_modules exists
