# DAMA Search and Filters

Release Pack N adds search and filter support.

## Backend Endpoints

Search projects:

    GET /search/projects

Supported query fields:

- query
- status
- project_type
- language
- limit
- offset

Search content assets:

    GET /search/content-assets

Supported query fields:

- query
- project_id
- status
- content_type
- source
- limit
- offset

## Frontend Routes

    /search
    /search/projects
    /search/content-assets
    /content-assets/[assetId]

## Safety

Search endpoints are read-only.

The content asset detail page links to export endpoints but does not execute destructive actions.
