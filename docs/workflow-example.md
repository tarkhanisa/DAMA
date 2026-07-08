# DAMA Project Workflow Example

This document shows a typical DAMA workflow.

## 1. Create Project

Endpoint:

    POST /projects

Example body:

    {
      "name": "DAMA Launch Campaign",
      "project_type": "content_campaign",
      "description": "Launch campaign for DAMA."
    }

## 2. Get Output Plan

Endpoint:

    GET /workflows/projects/{project_id}/output-plan

Purpose:

Create a plan from project content types.

## 3. Create Draft Assets

Endpoint:

    POST /workflows/projects/{project_id}/draft-assets

Purpose:

Create draft content asset records for the project.

## 4. Generate and Save One Asset

Endpoint:

    POST /workflows/projects/{project_id}/generate

Purpose:

Generate one project-aware content asset and store it.

## 5. Batch Generation Dry Run

Endpoint:

    POST /workflows/projects/{project_id}/batch-generate

Use dry run first:

    {
      "model": "qwen2.5-coder:7b",
      "dry_run": true,
      "max_outputs": 2
    }

## 6. Project Summary

Endpoint:

    GET /projects/{project_id}/summary

Purpose:

Review counts by status and content type.

## 7. Export Project Bundle

Endpoint:

    POST /exports/projects/{project_id}/bundle

Purpose:

Create Markdown bundle from all project content assets.

## 8. Backup Database

Endpoint:

    POST /maintenance/database/backup

Purpose:

Create local backup before major changes.
