# DAMA Frontend Routes

Super Pack J adds initial application routes.

## Routes

    /
    /projects
    /projects/[projectId]
    /content-assets

## Route Purpose

## /

Dashboard summary and developer quick links.

## /projects

Project list and basic project stats.

## /projects/[projectId]

Project detail shell, project summary, asset breakdowns, and workflow links.

## /content-assets

Content asset library with basic stats.

## Shared Components

- AppNav
- StatCard
- ReadinessPanel
- RecentList
- CountBreakdown
- LinkCard
- DataTable
- StatusPill

## API Client Coverage

The frontend API client now covers:

- dashboard summary
- frontend contract
- endpoint map
- runbook
- project list
- project detail
- project summary
- project content assets
- content asset list

## Super Pack K Routes

Added routes:

    /workflows
    /workflows/[projectId]
    /exports
    /maintenance

Purpose:

Expose workflow planning, export status, and maintenance status in the frontend shell.

## Super Pack M Routes

Added routes:

    /projects/new
    /content-assets/new
    /workflows/[projectId]/dry-run

Purpose:

Allow safe creation of projects, safe creation of manual content assets, and safe workflow dry-run previews.

## Release Pack N Routes

Added routes:

    /search
    /search/projects
    /search/content-assets
    /content-assets/[assetId]

Purpose:

Expose search, filters, and content asset detail pages.

## Release Pack O Routes

Added route:

    /operations

Updated routes:

    /projects/[projectId]
    /content-assets/[assetId]
    /maintenance

Purpose:

Expose confirmation-first safe operations for backup, export, and status changes.
