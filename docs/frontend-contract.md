# DAMA Frontend Contract

This document defines the first backend contract for a future DAMA dashboard.

## Base URL

    http://127.0.0.1:8000

## Interactive API Docs

    http://127.0.0.1:8000/docs

## OpenAPI JSON

    http://127.0.0.1:8000/openapi.json

## Recommended Frontend Sections

## Dashboard

Primary endpoints:

    GET /dashboard/summary
    GET /maintenance/status
    GET /system/status

## Projects

Primary endpoints:

    GET /projects
    POST /projects
    GET /projects/{project_id}
    GET /projects/{project_id}/summary
    PATCH /projects/{project_id}/status

## Content Assets

Primary endpoints:

    GET /content-assets
    POST /content-assets
    GET /content-assets/{asset_id}
    PATCH /content-assets/{asset_id}/status

## Workflows

Primary endpoints:

    GET /workflows/projects/{project_id}/output-plan
    POST /workflows/projects/{project_id}/draft-assets
    POST /workflows/projects/{project_id}/generate
    POST /workflows/projects/{project_id}/batch-generate

## Exports

Primary endpoints:

    POST /exports/content-assets/{asset_id}/markdown
    POST /exports/projects/{project_id}/bundle

## Developer

Primary endpoints:

    GET /developer/endpoint-map
    GET /developer/frontend-contract
    GET /developer/runbook

## Standard Error Shape

HTTP errors:

    {
      "error": {
        "type": "http_error",
        "status_code": 404,
        "message": "Project not found.",
        "path": "/projects/missing-project-id"
      }
    }

Validation errors:

    {
      "error": {
        "type": "validation_error",
        "status_code": 422,
        "message": "Request validation failed.",
        "path": "/projects",
        "details": []
      }
    }
