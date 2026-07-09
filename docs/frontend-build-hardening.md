# DAMA Frontend Build Hardening

Super Pack L prepares the frontend for real TypeScript and Next.js validation.

## Added

- formatter helpers
- shared PageHeader component
- shared ErrorPanel component
- TSX-safe generic DataTable
- ReactNode type import in layout
- frontend typecheck script
- optional npm typecheck in frontend-check

## Frontend Commands

Install dependencies:

    cd I:\DAMA\frontend
    npm install

Run typecheck:

    npm run typecheck

Run build:

    npm run build

## DAMA Autopilot Behavior

The DAMA frontend check always validates required files.

If frontend/node_modules exists, it also runs:

    npm run typecheck

If node_modules does not exist, it skips npm typecheck to keep backend-first development fast.

## Release Pack P Real Build

Release Pack P adds a real frontend build script:

    scripts/frontend-real-build.ps1

It runs:

    npm install
    npm run typecheck
    npm run build

It also adds backend CORS support for the local Next.js frontend:

    http://127.0.0.1:3000
    http://localhost:3000
    http://127.0.0.1:3001
    http://localhost:3001


## Webpack Build Stabilization

Next.js 16 uses Turbopack by default. Release Pack P stabilizes local builds by using:

    next dev --webpack
    next build --webpack

This avoids unclear Turbopack build-worker failures on the local Windows setup.


## Stable Frontend Version Pin

The frontend dependencies were pinned away from floating latest versions.

Current stabilized frontend line:

- next: 15
- react: 19
- react-dom: 19
- typescript: ^5.6.0

Reason:

The local Windows build with Next latest / Next 16 produced an unclear build-worker failure. The project now prioritizes stable reproducible builds over newest-version adoption.
