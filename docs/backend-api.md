# DAMA Backend API

DAMA is an AI content automation backend built with FastAPI.

This document describes the current backend API surface.

## Base URL

Local development:

http://127.0.0.1:8000

## Current Capabilities

- API index
- Local Ollama model discovery
- Raw text generation
- Prompt-template based generation
- Structured content generation
- Content type catalog
- AI provider catalog
- System status

---

## Root

### GET /

Returns basic application status.

Example response:

{
  "project": "DAMA",
  "status": "running"
}

---

## API Index

### GET /api

Returns a human-readable index of available backend capabilities.

Current capabilities:

- models
- generation
- content
- providers
- system

---

## Models

### GET /models

Returns locally available Ollama models.

Example response:

{
  "models": [
    {
      "name": "qwen2.5-coder:7b",
      "id": "dae161e27b0e",
      "size": "4.7 GB",
      "modified": "4 days ago"
    }
  ]
}

---

## Raw Text Generation

### POST /generate

Generates text using a supported AI provider.

Currently supported provider:

ollama

Direct prompt request:

{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "prompt": "Reply with exactly this text: DAMA_OK",
  "timeout": 120
}

Direct prompt response:

{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "response": "DAMA_OK"
}

Template request:

{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "template": "Write a {tone} post about {topic}.",
  "variables": {
    "tone": "professional",
    "topic": "DAMA"
  },
  "timeout": 120
}

Rules:

- Use either prompt or template, not both.
- If template is used, required variables must be provided.
- Unsupported providers return 400.
- Ollama runtime failures return 503.

---

## Content Types

### GET /content/types

Returns supported standard content types.

Current content type keys:

- blog_post
- social_caption
- product_description
- video_script
- email_campaign
- press_release

### GET /content/types/{key}

Returns one content type definition by key.

Example:

GET /content/types/social_caption

Invalid content type keys return 400.

---

## Structured Content Generation

### POST /content/generate

Generates production-oriented content using a standard content type.

Example request:

{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "topic": "DAMA AI content automation platform",
  "content_type": "product_description",
  "language": "English",
  "audience": "content teams",
  "timeout": 120
}

Example response:

{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "content_type": "product_description",
  "topic": "DAMA AI content automation platform",
  "language": "English",
  "tone": "persuasive",
  "content": "...",
  "prompt": "..."
}

Notes:

- content_type must be one of the supported standard content type keys.
- If tone is not provided, DAMA uses the default tone for the selected content type.
- If instructions is not provided, DAMA uses the default instructions for the selected content type.
- Invalid content type keys return 400.
- Missing required request fields return 422.

---

## Providers

### GET /providers

Returns supported AI providers.

Current provider:

- ollama

### GET /providers/{key}

Returns one provider definition by key.

Example:

GET /providers/ollama

Invalid provider keys return 400.

---

## System Status

### GET /system/status

Returns aggregated backend runtime status.

Example response:

{
  "app_name": "DAMA",
  "status": "healthy",
  "ollama": {
    "installed": true,
    "version": "0.23.0",
    "local_models_count": 1
  },
  "providers_count": 1,
  "content_types_count": 6,
  "errors": []
}

Possible status values:

- healthy
- degraded

---

## Local Testing

Run the fast backend smoke test:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\backend-check.ps1

The smoke test validates:

- Ollama installation
- Ollama version
- Local model listing
- Prompt rendering
- Provider catalog
- Content type catalog
- System status
- API index
- Model endpoint
- Provider endpoints
- Content type endpoints
- One real generation through /generate

---

## Current Backend Endpoint List

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

## Projects API

The project API prepares DAMA for project-based content workflows.

Current project endpoints:

GET /projects/types

GET /projects/types/{key}

POST /projects/metadata

Current supported project type keys:

- content_campaign
- product_launch
- video_package

Current note:

The project layer does not persist data yet. It prepares the future project record structure before database persistence is added.

## Content Assets API

The content asset API stores content outputs and connects them to projects.

POST /content-assets

Creates and stores a content asset.

GET /content-assets

Returns stored content assets.

GET /content-assets?project_id={project_id}

Returns content assets for one project.

GET /content-assets/{asset_id}

Returns one content asset by ID.

PATCH /content-assets/{asset_id}/status

Updates the content asset status.

Current content asset statuses:

- draft
- review
- approved
- published
- archived

Current content asset sources:

- manual
- ai_generated
- imported

## Generation Storage

POST /content/generate can optionally save generated output as a project-linked content asset.

Additional request fields:

project_id

Required when save_output is true.

save_output

Boolean. When true, generated content is stored as a content asset.

asset_title

Optional title for the saved content asset.

asset_status

Optional status for the saved content asset.

asset_metadata

Optional metadata dictionary for the saved content asset.

Example behavior:

- Generate structured content through the selected provider
- Return the generated response
- Store the generated response as a content asset when save_output is true
- Attach generation metadata to the stored content asset

Current source value for saved generations:

ai_generated

## Project Workflow Core

DAMA now supports project-level workflow operations.

Project workflow endpoints:

GET /projects/{project_id}/content-assets

Returns content assets connected to one project.

GET /projects/{project_id}/summary

Returns a project summary with:

- total_assets
- assets_by_status
- assets_by_content_type

PATCH /projects/{project_id}/status

Updates project workflow status.

Allowed project statuses:

- draft
- active
- review
- paused
- completed
- archived

## Generation Storage

POST /content/generate can optionally save generated output as a project-linked content asset.

Additional request fields:

project_id

Required when save_output is true.

save_output

Boolean. When true, generated content is stored as a content asset.

asset_title

Optional title for the saved content asset.

asset_status

Optional status for the saved content asset.

asset_metadata

Optional metadata dictionary for the saved content asset.

Current source value for saved generations:

ai_generated

## Workflow Automation API

The workflow automation API adds project-aware content planning and content asset preparation.

GET /workflows/projects/{project_id}/output-plan

Returns a planned content output list based on the project content types.

Query fields:

topic

Optional. Overrides the default generation topic.

POST /workflows/projects/{project_id}/draft-assets

Creates draft content assets based on the project content types.

Request fields:

topic

Optional. Used as the workflow topic.

title_prefix

Optional. Used as the title prefix for created draft assets.

POST /workflows/projects/{project_id}/generate

Generates content for a project and stores the output as a content asset.

Current note:

The workflow automation layer is intentionally simple. It does not use multi-agent execution yet.

## Export API

The export API creates Markdown files from stored DAMA content.

POST /exports/content-assets/{asset_id}/markdown

Exports one content asset as a Markdown file.

POST /exports/projects/{project_id}/bundle

Exports all content assets of one project as a Markdown bundle.

Current export directory:

backend/exports

The export directory is ignored by Git.

Current export format:

Markdown

## Batch Generation API

The batch generation API prepares or executes multiple project-aware content generations.

POST /workflows/projects/{project_id}/batch-generate

Request fields:

model

Required model name.

topic

Optional generation topic. Defaults to project name.

content_types

Optional list of content types to generate.

max_outputs

Optional maximum number of planned outputs. Current accepted range: 1 to 10.

dry_run

Boolean. Defaults to true.

When dry_run is true:

- no AI generation is executed
- no content asset is created
- a planned output list is returned

When dry_run is false:

- each planned output is generated
- each generated result is stored as a content asset
- execution summary is returned

Recommended use:

Start with dry_run true, review planned outputs, then execute with dry_run false.

## Dashboard API

The dashboard API provides an aggregated backend summary for future UI development.

GET /dashboard/summary

Returns:

- system status
- project totals
- project counts by status
- project counts by type
- recent projects
- content asset totals
- content asset counts by status
- content asset counts by content type
- content asset counts by source
- recent content assets
- export file summary
- readiness flags

Current readiness flags:

dashboard_ready

True when the dashboard API is available.

workflow_ready

True when the system has at least one project and one content asset.

export_ready

True when the system has at least one content asset.

## Maintenance API

The maintenance API provides local operational checks and database backup utilities.

GET /maintenance/status

Returns:

- database path
- database existence
- database size
- table row counts
- export directory status
- backup directory status
- maintenance readiness flag

POST /maintenance/database/backup

Creates a timestamped local SQLite database backup.

Current backup directory:

backend/backups

The backup directory is ignored by Git.

## Standard Error Shape

HTTP errors now use a standard shape:

error.type

Error category.

error.status_code

HTTP status code.

error.message

Human-readable message.

error.path

Request path.

Validation errors use:

error.type = validation_error

error.details

Validation detail list.

## Developer API

The developer API helps future frontend and operator workflows.

GET /developer/endpoint-map

Returns all FastAPI routes with path, methods, tags, name, and response model.

GET /developer/frontend-contract

Returns the first frontend contract for the future DAMA dashboard.

GET /developer/runbook

Returns the local operator runbook as structured JSON.
