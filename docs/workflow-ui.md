# DAMA Workflow, Export, and Maintenance UI

Super Pack K adds frontend pages for workflow operations, exports, and maintenance.

## Added Routes

    /workflows
    /workflows/[projectId]
    /exports
    /maintenance

## Workflow UI

The workflow index page lists projects and links to project workflow pages.

The project workflow page shows:

- project metadata
- output plan
- draft asset endpoint link
- batch generation endpoint link
- export bundle endpoint link
- raw output plan JSON

## Export UI

The export page shows:

- Markdown export count
- recent local export files
- project bundle export endpoints

## Maintenance UI

The maintenance page shows:

- database status
- table row counts
- export file status
- backup file status
- backup endpoint
- autopilot backup command

## Safety Note

Interactive POST buttons are intentionally not implemented yet.

For now, risky operations are shown as API endpoints or local commands so the operator remains in control.
