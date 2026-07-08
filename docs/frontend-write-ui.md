# DAMA Frontend Write UI Shells

Super Pack M adds safe write UI shells.

## Added Routes

    /projects/new
    /content-assets/new
    /workflows/[projectId]/dry-run

## Added Client Components

- CreateProjectForm
- CreateContentAssetForm
- WorkflowDryRunForm
- FormStatus

## Supported Safe Writes

## Create Project

Creates a new project through:

    POST /projects

## Create Content Asset

Creates a manual content asset through:

    POST /content-assets

## Workflow Dry Run

Runs safe batch planning only:

    POST /workflows/projects/{project_id}/batch-generate

With:

    dry_run = true

## Safety Rule

This pack does not add destructive actions.

It does not add delete buttons.

It does not add real batch generation execution from UI.

The workflow dry-run form always sends dry_run true.
