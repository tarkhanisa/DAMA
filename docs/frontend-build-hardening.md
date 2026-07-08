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
