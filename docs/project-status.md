# DAMA Project Status

This document tracks the current technical status of the DAMA project.

## Project

Name: DAMA

Goal:

DAMA is being developed as a production-grade AI Content Automation Platform.

The long-term goal is to become a lightweight AI operating platform for:

- AI content generation
- Prompt management
- Local LLM integration
- Image generation
- Publishing workflows
- Scheduling
- Agent-based workflows
- Dashboard
- REST API
- Plugin system

## Repository

GitHub:

https://github.com/tarkhanisa/DAMA

Local development path:

I:\DAMA

## Current Development Workflow

Local Development

Testing

Code Review

Commit

Push

## Current Backend Status

The backend is based on FastAPI.

The backend currently supports:

- API index
- Ollama local model listing
- Raw text generation
- Prompt-template based text generation
- Structured content generation
- Standard content type catalog
- AI provider catalog
- System status endpoint
- Fast smoke test script

## Current Backend Endpoints

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

## Current Backend Services

Current service files:

- backend/src/services/ollama_service.py
- backend/src/services/ai_service.py
- backend/src/services/prompt_service.py
- backend/src/services/content_service.py
- backend/src/services/system_service.py

## Current API Files

Current API files:

- backend/src/api/index.py
- backend/src/api/health.py
- backend/src/api/content.py
- backend/src/api/models.py
- backend/src/api/generate.py
- backend/src/api/content_generation.py
- backend/src/api/providers.py
- backend/src/api/system.py

## Current Ollama Status

Ollama is installed and available through PATH.

Tested Ollama version:

0.23.0

Current tested local model:

qwen2.5-coder:7b

## Current Content Types

Supported standard content type keys:

- blog_post
- social_caption
- product_description
- video_script
- email_campaign
- press_release

## Current AI Providers

Supported provider keys:

- ollama

## Current Test Script

Fast backend check:

scripts/backend-check.ps1

Run command:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-check.ps1

The fast smoke test checks:

- Ollama installation
- Ollama version
- Local model listing
- Prompt rendering
- Provider catalog
- Content type catalog
- System status
- API index
- Main backend endpoints
- One real generation through Ollama

## Current Documentation

Current documentation files:

- README.md
- docs/backend-api.md
- docs/project-status.md

## Last Completed Major Work

The README was updated to describe:

- DAMA project goal
- Current backend status
- Tech stack
- Local development
- Backend smoke test
- API endpoint list
- API documentation path
- Development workflow
- Roadmap

## Recommended Next Step

Next recommended development step:

Create a lightweight ProjectService.

Suggested file:

backend/src/services/project_service.py

Purpose:

Prepare the backend for future project-based content workflows.

Initial ProjectService should support:

- list project types
- define project metadata structure
- prepare future project creation endpoint
- avoid database dependency for now

Suggested future endpoints:

GET /projects/types

POST /projects

GET /projects/{id}

## Notes

Do not build the CLI yet.

Current priority remains:

Backend Services

REST API

Ollama Integration

Content Generation

Prompt Engine

Project Workflow Layer

## Macro Pack 1 Completed

Name:

Project Layer without database persistence

Added files:

- backend/src/services/project_service.py
- backend/src/api/projects.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

GET /projects/types

GET /projects/types/{key}

POST /projects/metadata

Purpose:

Prepare DAMA for project-based content workflows before database persistence is added.

Next recommended step:

Macro Pack 2: Persistence Layer

## Macro Pack 2 Completed

Name:

Persistence Layer

Added files:

- backend/src/database/sqlite_database.py
- backend/src/repositories/__init__.py
- backend/src/repositories/project_repository.py
- backend/tests/smoke_test_projects.py

Updated files:

- backend/src/api/projects.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md
- .gitignore

Added endpoints:

POST /projects

GET /projects

GET /projects/{project_id}

Purpose:

Move DAMA from temporary project metadata generation to persisted project records.

Persistence backend:

SQLite standard library.

Database file:

backend/data/dama.db

Next recommended step:

Macro Pack 3: Content Asset Layer

Suggested scope:

- content asset model
- content repository
- project-to-content relationship
- generated content storage
- content list/read endpoints
- smoke test update

## Macro Pack 3 Completed

Name:

Content Asset Layer

Added files:

- backend/src/services/content_asset_service.py
- backend/src/repositories/content_asset_repository.py
- backend/src/api/content_assets.py
- backend/tests/smoke_test_content_assets.py

Updated files:

- backend/src/database/sqlite_database.py
- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

POST /content-assets

GET /content-assets

GET /content-assets?project_id={project_id}

GET /content-assets/{asset_id}

PATCH /content-assets/{asset_id}/status

Purpose:

Allow DAMA to store content outputs as project-linked assets.

Next recommended step:

Macro Pack 4: Generation History and Save Generated Output

Suggested scope:

- connect /content/generate to persisted content assets
- add optional project_id and save_output fields
- store AI-generated content as content asset
- add generation metadata
- update smoke tests

## Macro Pack 4 Completed

Name:

Generation Storage

Updated files:

- backend/src/api/content_generation.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added files:

- backend/tests/smoke_test_generation_storage.py

Updated behavior:

POST /content/generate can now save generated output as a project-linked content asset.

New request fields:

- project_id
- save_output
- asset_title
- asset_status
- asset_metadata

Purpose:

Connect content generation to persistent project assets.

Next recommended step:

Macro Pack 5: Project Content Workflow

Suggested scope:

- project detail endpoint with attached content assets
- project summary endpoint
- project status updates
- content counts per project
- workflow-ready project state

## Mega Pack A Completed

Name:

Project Workflow Core

Updated files:

- backend/src/services/project_service.py
- backend/src/repositories/project_repository.py
- backend/src/api/projects.py
- backend/src/api/content_generation.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added files:

- backend/tests/smoke_test_generation_storage.py
- backend/tests/smoke_test_project_workflow.py

Added behavior:

- POST /content/generate can save output into content assets
- GET /projects/{project_id}/content-assets
- GET /projects/{project_id}/summary
- PATCH /projects/{project_id}/status

Purpose:

Move DAMA from simple storage into project workflow core.

Next recommended Mega Pack:

Mega Pack B: Content Workflow Automation

Suggested scope:

- generate and save content through project-aware workflow endpoint
- create content asset drafts from project type defaults
- add project output plan endpoint
- add batch generation preparation
- avoid multi-agent logic for now

## Mega Pack B Completed

Name:

Content Workflow Automation

Added files:

- backend/src/services/workflow_service.py
- backend/src/api/workflows.py
- backend/tests/smoke_test_workflow_automation.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

GET /workflows/projects/{project_id}/output-plan

POST /workflows/projects/{project_id}/draft-assets

POST /workflows/projects/{project_id}/generate

Purpose:

Move DAMA from project workflow storage to project-aware content workflow automation.

Next recommended Mega Pack:

Mega Pack C: Export Layer

Suggested scope:

- export content asset as markdown
- export project content bundle
- add local export directory
- add export repository/service
- add smoke test

## Mega Pack C Completed

Name:

Export Layer

Added files:

- backend/src/services/export_service.py
- backend/src/api/exports.py
- backend/tests/smoke_test_exports.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md
- .gitignore

Added endpoints:

POST /exports/content-assets/{asset_id}/markdown

POST /exports/projects/{project_id}/bundle

Purpose:

Allow DAMA to produce usable Markdown files from stored content assets and projects.

Current export directory:

backend/exports

Next recommended Mega Pack:

Mega Pack D: Project-Aware Generation Batch

Suggested scope:

- batch generation request from project output plan
- create multiple generated assets in one call
- dry-run mode
- execution summary
- safer timeout handling

## Mega Pack D Completed

Name:

Project-Aware Batch Generation

Updated files:

- backend/src/services/workflow_service.py
- backend/src/api/workflows.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added files:

- backend/tests/smoke_test_batch_generation.py

Added endpoint:

POST /workflows/projects/{project_id}/batch-generate

Added behavior:

- dry-run batch generation planning
- content type filtering
- max output limiting
- optional execution mode
- generated content asset storage when dry_run is false

Purpose:

Allow DAMA to prepare and eventually execute multiple project-aware content generations in one workflow call.

Next recommended Mega Pack:

Mega Pack E: Dashboard Readiness API

Suggested scope:

- aggregate dashboard summary endpoint
- counts for projects, assets, statuses, exports
- recent projects
- recent content assets
- system + workflow readiness summary

## Mega Pack E Completed

Name:

Dashboard Readiness API

Added files:

- backend/src/services/dashboard_service.py
- backend/src/api/dashboard.py
- backend/tests/smoke_test_dashboard.py

Updated files:

- backend/src/api/__init__.py
- backend/src/main.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoint:

GET /dashboard/summary

Purpose:

Prepare DAMA for future frontend/dashboard development by exposing one aggregated operational summary endpoint.

Next recommended Mega Pack:

Mega Pack F: API Quality and Error Standardization

Suggested scope:

- standard API error payload
- request validation consistency
- response envelope decision
- lightweight API quality docs
- smoke tests for common error shapes

## Super Pack F Completed

Name:

API Quality + Maintenance + Developer Readiness

Added files:

- backend/src/services/maintenance_service.py
- backend/src/api/maintenance.py
- backend/tests/smoke_test_maintenance.py

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md
- .gitignore

Added endpoints:

GET /maintenance/status

POST /maintenance/database/backup

Added behavior:

- standardized HTTP error payload
- standardized validation error payload
- database status reporting
- export directory status reporting
- backup directory status reporting
- local SQLite backup creation
- cleaner backend-check smoke test runner

Purpose:

Make DAMA more maintainable, dashboard-ready, and safer to continue developing at higher speed.

Next recommended Super Pack:

Super Pack G: API Documentation + OpenAPI Readiness + Local Operator Guide

Suggested scope:

- generated endpoint map
- local operator guide
- backend runbook
- system lifecycle docs
- project workflow example docs
- frontend readiness contract

## Super Pack G Completed

Name:

Developer Readiness + Frontend Contract + Operator Docs

Added files:

- backend/src/services/developer_service.py
- backend/src/api/developer.py
- backend/tests/smoke_test_developer.py
- docs/operator-guide.md
- docs/frontend-contract.md
- docs/workflow-example.md

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- backend/src/api/index.py
- scripts/backend-check.ps1
- docs/backend-api.md
- docs/project-status.md

Added endpoints:

GET /developer/endpoint-map

GET /developer/frontend-contract

GET /developer/runbook

Purpose:

Prepare DAMA for faster frontend development, easier local operation, and cleaner developer handoff.

Next recommended Super Pack:

Super Pack H: Frontend Foundation

Suggested scope:

- create frontend package baseline
- create simple dashboard structure
- define API client
- define page map
- no heavy UI framework decision beyond current project stack unless confirmed

## Super Pack H Completed

Name:

Autopilot Runner + Frontend Foundation

Added files:

- scripts/dama.ps1
- scripts/dama-check.ps1
- scripts/dama-ship.ps1
- scripts/frontend-check.ps1
- frontend/package.json
- frontend/next.config.mjs
- frontend/tsconfig.json
- frontend/README.md
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/app/layout.tsx
- frontend/src/app/page.tsx
- frontend/src/app/globals.css
- docs/development-workflow.md
- docs/frontend-foundation.md

Purpose:

Reduce repetitive manual development steps and prepare DAMA for faster frontend implementation.

## API Capability Compatibility Hotfix

The API index endpoint now returns capabilities in two formats:

- capabilities: list format for backward compatibility with smoke tests
- capabilities_by_key: dictionary format for frontend and developer usage

Purpose:

Keep old checks stable while preserving key-based API discovery.

## Super Pack I Completed

Name:

Real Dashboard UI

Added files:

- frontend/src/components/stat-card.tsx
- frontend/src/components/readiness-panel.tsx
- frontend/src/components/recent-list.tsx
- frontend/src/components/count-breakdown.tsx
- frontend/src/components/link-card.tsx
- docs/dashboard-ui.md

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-foundation.md
- docs/project-status.md

Added behavior:

- dashboard data fetching
- backend unavailable fallback
- readiness UI
- summary stat cards
- recent project list
- recent content asset list
- developer quick links

Purpose:

Move DAMA frontend from static foundation to real dashboard UI backed by API data.

Next recommended Super Pack:

Super Pack J: Projects UI + Content Assets UI

Suggested scope:

- project list page
- project detail page shell
- content asset list page
- API client extensions
- frontend route map docs

## Super Pack J Completed

Name:

Projects UI + Content Assets UI

Added files:

- frontend/src/components/app-nav.tsx
- frontend/src/components/status-pill.tsx
- frontend/src/components/data-table.tsx
- frontend/src/app/projects/page.tsx
- frontend/src/app/projects/[projectId]/page.tsx
- frontend/src/app/content-assets/page.tsx
- docs/frontend-routes.md

Updated files:

- frontend/src/app/layout.tsx
- frontend/src/app/globals.css
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- scripts/frontend-check.ps1
- docs/frontend-foundation.md
- docs/project-status.md

Added behavior:

- frontend navigation
- project list UI
- project detail UI shell
- content asset library UI
- frontend API client extensions
- stronger frontend structure checks

Purpose:

Move DAMA frontend from dashboard-only to an initial multi-page application shell.

Next recommended Super Pack:

Super Pack K: Workflow UI + Export UI + Maintenance UI

Suggested scope:

- workflow page
- output plan viewer
- batch dry-run form shell
- export links
- maintenance status page
- backup trigger note or safe manual link

## Super Pack K Completed

Name:

Workflow UI + Export UI + Maintenance UI

Added files:

- frontend/src/components/action-card.tsx
- frontend/src/components/json-preview.tsx
- frontend/src/app/workflows/page.tsx
- frontend/src/app/workflows/[projectId]/page.tsx
- frontend/src/app/exports/page.tsx
- frontend/src/app/maintenance/page.tsx
- docs/workflow-ui.md

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- workflow project selection page
- project workflow output plan page
- export center page
- maintenance center page
- extended frontend API client
- extended navigation
- safer UI by linking POST operations instead of executing them directly

Purpose:

Move DAMA frontend into a broader operational dashboard that covers workflow, export, and maintenance surfaces.

Next recommended Super Pack:

Super Pack L: Frontend Build Hardening + TypeScript Validation

Suggested scope:

- add frontend install/build docs
- add optional npm build check when node_modules exists
- add TypeScript/Next compatibility fixes
- fix dynamic route typing if needed
- improve API client error display

## Super Pack L Completed

Name:

Frontend Build Hardening + TypeScript Validation

Added files:

- frontend/src/lib/formatters.ts
- frontend/src/components/page-header.tsx
- frontend/src/components/error-panel.tsx
- docs/frontend-build-hardening.md

Updated files:

- frontend/src/components/data-table.tsx
- frontend/src/app/layout.tsx
- frontend/src/app/page.tsx
- frontend/src/app/maintenance/page.tsx
- frontend/package.json
- scripts/frontend-check.ps1
- docs/frontend-foundation.md
- docs/project-status.md

Added behavior:

- TSX-safe generic table component
- shared error panel
- shared page header
- number and byte formatting helpers
- optional npm typecheck when node_modules exists
- stronger frontend hardening checks

Purpose:

Prepare DAMA frontend for real dependency installation, TypeScript validation, and Next.js build checks.

Next recommended Super Pack:

Super Pack M: API Write UI Shells

Suggested scope:

- safe project create form shell
- content asset create form shell
- workflow dry-run form shell
- no destructive actions
- client component split where needed

## Super Pack M Completed

Name:

API Write UI Shells

Added files:

- frontend/src/components/form-status.tsx
- frontend/src/components/create-project-form.tsx
- frontend/src/components/create-content-asset-form.tsx
- frontend/src/components/workflow-dry-run-form.tsx
- frontend/src/app/projects/new/page.tsx
- frontend/src/app/content-assets/new/page.tsx
- frontend/src/app/workflows/[projectId]/dry-run/page.tsx
- docs/frontend-write-ui.md

Updated files:

- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/app/projects/page.tsx
- frontend/src/app/content-assets/page.tsx
- frontend/src/app/workflows/[projectId]/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- safe project creation UI
- safe manual content asset creation UI
- safe workflow dry-run UI
- API client write methods
- frontend form styles
- stronger frontend write UI checks

Purpose:

Move DAMA frontend from read-only dashboard to safe operator write workflows.

Next recommended Super Pack:

Super Pack N: Backend Pagination + Search + Frontend Filters

Suggested scope:

- query filters for projects and assets
- search by title/name
- status filters
- frontend filter UI
- safer list scaling

## Release Pack N Completed

Name:

Search + Filters + Content Asset Detail + Export UX

Added backend files:

- backend/src/services/search_service.py
- backend/src/api/search.py
- backend/tests/smoke_test_search.py

Added frontend files:

- frontend/src/components/search-filter-card.tsx
- frontend/src/components/asset-body-preview.tsx
- frontend/src/app/search/page.tsx
- frontend/src/app/search/projects/page.tsx
- frontend/src/app/search/content-assets/page.tsx
- frontend/src/app/content-assets/[assetId]/page.tsx

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- scripts/backend-check.ps1
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/components/app-nav.tsx
- frontend/src/app/projects/page.tsx
- frontend/src/app/content-assets/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/backend-api.md
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- read-only backend search API
- project search filters
- content asset search filters
- frontend search pages
- content asset detail page
- asset markdown export endpoint link
- stronger frontend check
- backend smoke test for search

Next recommended Release Pack:

Release Pack O: Operational Actions and Safe POST UI

Suggested scope:

- safe export trigger UI
- safe backup trigger UI
- project status update UI
- content asset status update UI
- confirmation-first UI actions
- no delete operations

## Release Pack O Completed

Name:

Safe Operational Actions UI

Added frontend files:

- frontend/src/components/safe-action-button.tsx
- frontend/src/components/operation-result.tsx
- frontend/src/components/backup-action.tsx
- frontend/src/components/export-project-action.tsx
- frontend/src/components/export-content-asset-action.tsx
- frontend/src/components/project-status-form.tsx
- frontend/src/components/content-asset-status-form.tsx
- frontend/src/app/operations/page.tsx
- docs/safe-operations-ui.md

Updated files:

- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/components/app-nav.tsx
- frontend/src/app/projects/[projectId]/page.tsx
- frontend/src/app/content-assets/[assetId]/page.tsx
- frontend/src/app/maintenance/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- confirmation-first backup action
- confirmation-first project bundle export
- confirmation-first content asset markdown export
- project status update UI
- content asset status update UI
- operations center
- no delete operations

Next recommended Release Pack:

Release Pack P: Frontend Dependency Install + Real Typecheck Fixes

Suggested scope:

- run npm install
- run npm typecheck
- fix real TypeScript/Next errors
- run npm build if feasible
- add lockfile if generated

## Release Pack P Completed

Name:

Real Frontend Install + TypeScript Fix + Build Validation

Added files:

- scripts/frontend-real-build.ps1

Updated files:

- backend/src/main.py
- frontend/src/components/page-header.tsx
- frontend/src/components/search-filter-card.tsx
- frontend/src/components/create-project-form.tsx
- frontend/src/components/create-content-asset-form.tsx
- frontend/src/components/workflow-dry-run-form.tsx
- frontend/src/components/project-status-form.tsx
- frontend/src/components/content-asset-status-form.tsx
- frontend/src/app/projects/[projectId]/page.tsx
- frontend/src/app/workflows/[projectId]/page.tsx
- frontend/src/app/workflows/[projectId]/dry-run/page.tsx
- docs/frontend-build-hardening.md
- docs/project-status.md

Added behavior:

- local CORS support for frontend to backend API calls
- TSX-safe ReactNode imports
- FormEvent type imports for client components
- Next dynamic route params compatibility
- real frontend install/typecheck/build script

Purpose:

Move frontend validation from file-existence checks to real Next.js/TypeScript build validation.


## Frontend Webpack Build Hotfix

The frontend build script was stabilized by switching Next.js build/dev commands to Webpack:

- next dev --webpack
- next build --webpack

Reason:

Next.js 16.2 local Turbopack build failed with an unclear build worker error.


## Frontend Stable Version Pin

Frontend dependencies were stabilized by replacing floating latest versions with a Next 15 line.

Reason:

Next latest / Next 16 produced an unclear local build-worker failure on Windows.

Goal:

Make frontend install, typecheck, and build reproducible before adding more UI features.

## Release Pack Q Completed

Name:

Repo Cleanup + Production Readiness

Added files:

- scripts/dev-backend.ps1
- scripts/dev-frontend.ps1
- scripts/dev-all.ps1
- scripts/repo-hygiene-check.ps1
- docs/local-development.md
- docs/production-readiness.md
- docs/repo-hygiene.md

Updated files:

- .gitignore
- README.md
- frontend/tsconfig.json
- scripts/frontend-check.ps1
- docs/project-status.md

Cleaned:

- frontend/tsconfig.tsbuildinfo removed from working tree
- frontend/tsconfig.tsbuildinfo ignored

Added behavior:

- local backend start script
- local frontend start script
- local full-stack start script
- repo hygiene check
- stronger frontend production-readiness check

Next recommended Release Pack:

Release Pack R: Dependency Audit + Security Baseline

Suggested scope:

- npm audit review
- safe non-breaking npm audit handling
- backend dependency freeze
- requirements lock snapshot
- security docs
- no force upgrades without review

## Release Pack R Completed

Name:

Dependency Audit + Security Baseline

Added files:

- scripts/dependency-audit.ps1
- scripts/security-baseline-check.ps1
- docs/security-baseline.md
- docs/dependency-policy.md
- docs/dependency-snapshots/README.md

Updated files:

- scripts/dama-check.ps1
- README.md
- docs/production-readiness.md
- docs/repo-hygiene.md
- docs/project-status.md

Added behavior:

- security baseline check
- dependency audit snapshot script
- high/critical npm audit threshold
- backend pip freeze snapshot generation
- frontend dependency tree snapshot generation
- pinned dependency policy docs
- no-force audit policy

Next recommended Release Pack:

Release Pack S: Backend Requirements Lock + Config Hardening

Suggested scope:

- backend requirements freeze snapshot
- config validation improvements
- environment docs
- .env.example review
- production config checklist

## Release Pack S Completed

Name:

Backend Requirements Lock + Config Hardening

Added files:

- .env.example
- scripts/config-baseline-check.ps1
- scripts/backend-requirements-snapshot.ps1
- docs/configuration.md
- docs/environment-checklist.md
- docs/backend-requirements-policy.md

Updated files:

- .gitignore
- README.md
- scripts/dama-check.ps1
- docs/production-readiness.md
- docs/security-baseline.md
- docs/project-status.md

Added behavior:

- config baseline check
- env file safety check
- frontend API env validation
- backend CORS validation
- backend dependency snapshot script

Next recommended Release Pack:

Release Pack T: Runtime Health UI + Dev Operator Dashboard

Suggested scope:

- frontend health page polish
- backend/frontend connection diagnostics
- Ollama model status panel
- database backup status panel
- environment status summary
- no destructive actions

## Release Pack T Completed

Name:

Runtime Health UI + Dev Operator Dashboard

Added files:

- backend/src/api/runtime.py
- backend/tests/smoke_test_runtime.py
- frontend/src/app/runtime/page.tsx
- docs/runtime-health.md

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- README.md
- docs/production-readiness.md
- docs/project-status.md

Added behavior:

- GET /runtime/health
- read-only runtime frontend page
- Ollama reachability diagnostics
- storage path diagnostics
- safe public config summary
- runtime smoke test

Next recommended Release Pack:

Release Pack U: AI Generation Operator UI

Suggested scope:

- safe single-content generation page
- model list selector
- project selector
- content type selector
- save_output toggle
- generated asset link
- no batch execution from UI yet

## Release Pack U Completed

Name:

AI Generation Operator UI

Added files:

- frontend/src/app/generate/page.tsx
- frontend/src/components/generate-content-form.tsx
- docs/ai-generation-operator.md

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- README.md
- docs/production-readiness.md
- docs/project-status.md

Added behavior:

- safe single generation UI
- project selector
- content type selector
- model selector
- brief input
- save_output toggle
- result preview
- saved asset link when available
- fallback from content generation endpoint to workflow generation endpoint

Next recommended Release Pack:

Release Pack V: Project Workspace Polish

Suggested scope:

- project workspace tabs
- assets inside project detail
- generation shortcut inside project page
- workflow dry-run shortcut
- export shortcut
- clearer operator flow per project

## Release Pack V Completed

Name:

Persian Simple UX + Quality Generation

Added files:

- docs/persian-simple-ux-and-quality-generation.md

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/app/page.tsx
- frontend/src/app/projects/page.tsx
- frontend/src/app/generate/page.tsx
- frontend/src/components/generate-content-form.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- Persian operator navigation
- Persian simple dashboard
- Persian project list
- Persian generation form
- quality-focused prompt wrapper
- audience/tone/purpose/output-format fields
- safer high-quality generation defaults

Next recommended Release Pack:

Release Pack W: Project Workspace Polish

Suggested scope:

- make each project page simpler and Persian
- show project assets inside project page
- add direct generate-for-this-project button
- add recent outputs panel
- add export shortcuts

## Release Pack W Completed

Name:

Publishing Foundation + Channel Registry

Added files:

- backend/src/services/publishing_channel_service.py
- backend/src/api/publishing.py
- backend/tests/smoke_test_publishing.py
- frontend/src/app/publishing/page.tsx
- frontend/src/components/create-publishing-channel-form.tsx
- docs/publishing-foundation.md

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- frontend/src/components/app-nav.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- publishing channel registry
- channel creation API
- channel listing API
- channel test placeholder API
- Persian publishing page
- safe no-secret channel registration

Next recommended Release Pack:

Release Pack X: Channel Variant Generator

Suggested scope:

- choose content asset
- choose destination channels
- generate adapted variants
- WordPress version
- Telegram version
- Instagram caption version
- LinkedIn version
- manual review status

## Release Pack X Completed

Name:

Channel Variant Generator

Added files:

- backend/src/services/publishing_variant_service.py
- backend/tests/smoke_test_publishing_variants.py
- frontend/src/app/publishing/variants/page.tsx
- frontend/src/components/create-publishing-variants-form.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- list publishing variants
- create channel-specific variant plan
- update variant status
- Persian variant-generation UI
- one content asset to many channel variants
- no real publishing yet

Next recommended Release Pack:

Release Pack Y: AI Variant Enhancer

Suggested scope:

- use local AI to improve each channel variant
- channel-specific prompt templates
- WordPress SEO draft fields
- Telegram message polish
- Instagram caption polish
- LinkedIn professional rewrite
- still no automatic publishing

## Release Pack Y Completed

Name:

AI Variant Enhancer

Added files:

- backend/src/services/publishing_variant_ai_service.py
- backend/tests/smoke_test_publishing_ai_enhancer.py
- frontend/src/components/enhance-publishing-variant-action.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/page.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- enhance publishing variant endpoint
- dry-run enhancement
- Ollama enhancement mode
- channel-specific rewrite prompts
- safe fallback when Ollama is unavailable
- frontend action to enhance a variant

Next recommended Release Pack:

Release Pack Z: Publishing Review + Approval Workflow

Suggested scope:

- variant detail page
- approve/reject variant
- ready_for_publish status
- review notes
- compare source vs variant
- no real publishing yet

## Release Pack Z Completed

Name:

Publishing Review + Approval Workflow

Added files:

- backend/tests/smoke_test_publishing_review.py
- frontend/src/app/publishing/variants/[variantId]/page.tsx
- frontend/src/components/review-publishing-variant-form.tsx

Updated files:

- backend/src/services/publishing_variant_service.py
- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/page.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- review publishing variant endpoint
- variant detail page
- compare source vs channel variant
- edit variant title/body
- approve/reject variant
- ready_for_publish status
- review notes
- review history

Next recommended Release Pack:

Release Pack AA: WordPress Draft Connector

Suggested scope:

- WordPress channel configuration shape
- no secret in database
- manual environment-based application password support
- create draft post from approved variant
- store publish attempt
- no automatic publish yet

## Release Pack AA Completed

Name:

WordPress Draft Connector

Added files:

- backend/src/services/wordpress_draft_connector_service.py
- backend/tests/smoke_test_wordpress_draft_connector.py
- frontend/src/components/create-wordpress-draft-action.tsx
- frontend/src/app/publishing/attempts/page.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/[variantId]/page.tsx
- frontend/src/components/app-nav.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- .env.example
- docs/publishing-foundation.md
- docs/configuration.md
- docs/project-status.md

Added behavior:

- WordPress draft connector
- dry-run mode
- real WordPress draft mode through environment variables
- publishing attempts log
- frontend action on variant detail page
- publishing attempts page

Next recommended Release Pack:

Release Pack AB: WordPress Config Helper + Draft Validation

Suggested scope:

- WordPress connection test endpoint
- safer config diagnostics
- better error messages
- post category/tag draft fields
- SEO field placeholders
- no direct publish yet

## Release Pack AC Completed

Name:

Real WordPress Draft Flow Polish

Added files:

- backend/tests/smoke_test_wordpress_flow_polish.py
- frontend/src/app/publishing/attempts/[attemptId]/page.tsx

Updated files:

- backend/src/services/wordpress_draft_connector_service.py
- frontend/src/components/create-wordpress-draft-action.tsx
- frontend/src/app/publishing/attempts/page.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- .env.example
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- attempt detail page
- WordPress draft link support
- improved connector error details
- SEO title / meta description request preview
- optional SEO meta sending flag

Next recommended Release Pack:

Release Pack AD: Real WordPress Draft Test Setup

Suggested scope:

- step-by-step real WordPress env setup
- WordPress application password checklist
- real authentication test
- one real draft creation flow
- no direct publish yet

## Release Pack AD Completed

Name:

Backend Local Env Loader + Real WordPress Test Checklist

Added files:

- backend/src/core/__init__.py
- backend/src/core/env_loader.py
- backend/tests/smoke_test_local_env_loader.py
- backend/.env.local.example
- docs/real-wordpress-draft-test.md

Updated files:

- backend/src/main.py
- scripts/backend-check.ps1
- .gitignore
- .env.example
- docs/configuration.md
- docs/project-status.md

Added behavior:

- backend loads local env files automatically
- WordPress credentials can be stored locally in backend/.env.local
- local env files are ignored by git
- smoke test validates env loading
- real WordPress draft checklist added

Next recommended Release Pack:

Release Pack AE: Real WordPress Draft Test Run

Suggested scope:

- choose target WordPress site
- create Application Password
- configure backend/.env.local
- test /publishing/wordpress
- create one real WordPress draft
- no direct publish yet

## Release Pack AF Completed

Name:

Telegram Preview / Test Send

Added files:

- backend/src/services/telegram_connector_service.py
- backend/tests/smoke_test_telegram_connector.py
- frontend/src/app/publishing/telegram/page.tsx
- frontend/src/components/telegram-connection-test-action.tsx
- frontend/src/components/telegram-preview-test-send-action.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/[variantId]/page.tsx
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- backend/.env.local.example
- .env.example
- docs/configuration.md
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- Telegram config status endpoint
- Telegram dry-run/real bot test endpoint
- Telegram preview for publishing variants
- Telegram dry-run send-test attempt
- Telegram real send-test path
- frontend Telegram status page
- variant detail action for Telegram preview/test send

Next recommended Release Pack:

Release Pack AG: Telegram Real Test Setup

Suggested scope:

- create Telegram bot
- configure backend/.env.local
- dry-run from UI
- real getMe test
- send one real test message to private test channel/group
- no scheduled public publishing yet

## Release Pack AH Completed

Name:

Publishing Queue

Added files:

- backend/src/services/publishing_queue_service.py
- backend/tests/smoke_test_publishing_queue.py
- frontend/src/app/publishing/queue/page.tsx
- frontend/src/components/create-publishing-queue-item-form.tsx
- frontend/src/components/run-publishing-queue-item-action.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/components/app-nav.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- manual publishing queue
- add approved/ready variants to queue
- run queue item manually
- WordPress and Telegram connector execution
- dry-run default
- queue status tracking
- attempt linking

Next recommended Release Pack:

Release Pack AI: Multi-channel Publish Dashboard

Suggested scope:

- one page for content asset  variants  queue
- select multiple channels
- generate variants
- add all to queue
- run dry-run batch
- no fully automatic public publishing yet

## Release Pack AI-0 Completed

Name:

Persian Minimal Operator UX + Runtime Cleanup

Added files:

- frontend/src/app/settings/page.tsx
- frontend/src/app/advanced/page.tsx
- scripts/cleanup_operator_runtime_data.py

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/app/page.tsx
- frontend/src/app/publishing/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- simplified Persian navigation
- cleaner daily dashboard
- simplified publishing center
- settings page for WordPress and Telegram
- advanced section for technical pages
- safe runtime cleanup script with backup
- clean default WordPress and Telegram channels

Next recommended Release Pack:

Release Pack AI: Multi-channel Publish Dashboard

Suggested scope:

- one central workflow page
- choose content asset
- choose channels
- create variants
- add to queue
- run dry-run batch

## Release Pack AI-1 Completed

Name:

Persian UX Polish + Visual Dashboard Schematic

Added files:

- frontend/src/lib/persian-copy.ts
- scripts/audit_frontend_persian_copy.py

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/publishing/queue/page.tsx
- frontend/src/app/settings/page.tsx
- frontend/src/components/create-publishing-queue-item-form.tsx
- frontend/src/components/run-publishing-queue-item-action.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- centralized Persian copy helpers
- visual schematic dashboard flow
- clearer daily operator dashboard
- Persian labels for queue status, attempt status, connectors and run modes
- clearer publishing queue page
- clearer queue form buttons and messages
- frontend copy audit report for remaining English UI copy

Next recommended step:

Use docs/frontend-copy-audit.md to polish remaining WordPress, Telegram, variants and attempt pages.

## Release Pack AI-2 Completed

Name:

Persian Attempts & Technical Details Polish

Updated files:

- frontend/src/lib/persian-copy.ts
- frontend/src/app/publishing/attempts/page.tsx
- frontend/src/app/publishing/attempts/[attemptId]/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- Persian labels for publishing attempts
- simplified attempts list
- simplified attempt detail page
- technical JSON moved behind collapsible details
- better Persian error summaries
- safer frontend check using LiteralPath for dynamic route folders

Next recommended step:

Release Pack AI-3: Smart Test Data Cleanup

Goal:

- remove only smoke/test queue items, variants and attempts
- preserve clean real WordPress and Telegram channels
- add a button/page in Advanced for safe cleanup

## Release Pack AI-3 Completed

Name:

Smart Test Data Cleanup

Added files:

- backend/src/services/runtime_cleanup_service.py
- scripts/cleanup_test_runtime_data.py
- frontend/src/components/cleanup-test-data-action.tsx
- frontend/src/app/advanced/cleanup/page.tsx

Updated files:

- backend/src/api/publishing.py
- backend/tests/smoke_test_publishing_queue.py
- frontend/src/app/advanced/page.tsx
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- preview test runtime cleanup
- run test runtime cleanup with backup
- preserve clean real WordPress and Telegram channels
- remove smoke/test channels, variants, attempts and queue items
- publishing queue smoke test cleans its own runtime artifacts
- advanced cleanup page for safe manual cleanup

Next recommended step:

Release Pack AI-4: Guided Operator Checklist

Goal:

- show a step-by-step checklist in the UI
- guide the user from content generation to variants, queue and report review
- make the panel feel less like a technical dashboard and more like an operator console

## Release Pack AI-4 Completed

Name:

Guided Operator Checklist

Added files:

- frontend/src/lib/operator-workflow.ts
- frontend/src/components/operator-checklist.tsx

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- guided operator checklist on dashboard
- automatic next action suggestion
- dashboard now reads connector, variant, queue and attempt status
- clear five-step daily workflow
- warning state when queue or attempts need review
- simpler operator console behavior before adding bigger multi-channel dashboard

Next recommended step:

Release Pack AI-5: Variants Page Persian Polish

Goal:

- simplify and Persian-polish the variants page
- make review/approval flow clearer
- add "send to queue" path from variant detail

## Release Pack AI-5 Completed

Name:

Media Campaign Composer

Added files:

- backend/src/services/media_campaign_service.py
- backend/tests/smoke_test_media_campaigns.py
- frontend/src/components/create-media-campaign-form.tsx
- frontend/src/app/publishing/campaigns/page.tsx
- frontend/src/app/publishing/campaigns/[campaignId]/page.tsx

Updated files:

- backend/src/api/publishing.py
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- frontend/src/app/publishing/page.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- create media campaign with project name
- write master caption/body
- add image/video paths or URLs
- select destination channels
- list campaigns
- view campaign detail
- store campaign runtime data locally

Next recommended step:

Release Pack AI-6: Campaign-to-Variants Planner

Goal:

- select a campaign
- generate variants for all selected channels
- link variants back to campaign
- prepare the bridge toward multi-channel queue publishing

## Release Pack AI-6 Completed

Name:

Three-Door Operator Console + Publish Wizard

Added files:

- frontend/src/app/produce/page.tsx
- frontend/src/app/other/page.tsx
- frontend/src/components/simple-publish-wizard-form.tsx

Updated files:

- frontend/src/app/page.tsx
- frontend/src/app/publishing/page.tsx
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/project-status.md

Added behavior:

- dashboard reduced to three main doors: Produce, Publish, Other
- production area separated from publishing
- publishing starts with project/context question
- publishing wizard creates a media campaign
- reports, settings, cleanup, backups and technical tools moved to Other
- top navigation simplified dramatically

Next recommended step:

Release Pack AI-7: Campaign-to-Variants Planner

Goal:

- after a campaign is created, generate platform-specific variants for selected channels
- link generated variants back to the campaign
- then add those variants to the publishing queue
