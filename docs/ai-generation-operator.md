# DAMA AI Generation Operator

Release Pack U adds a safe single-generation operator UI.

## Frontend Page

    http://localhost:3000/generate

## Behavior

The page supports:

- choosing a project
- choosing a content type
- choosing a model
- writing a brief
- toggling `save_output`
- generating one result at a time
- opening the saved content asset when the backend returns an asset id

## Safety

This page intentionally does not expose:

- batch generation
- destructive actions
- delete operations
- background queues
- automatic mass publishing

## Backend Calls

The UI first tries:

    POST /content/generate

If that endpoint rejects the payload, it tries the project workflow endpoint:

    POST /workflows/projects/{project_id}/generate

This gives the operator UI compatibility with the current backend generation surface while the backend contract continues to evolve.

## Requirement

For real generation, Ollama should be running locally and the selected model should exist.

Recommended local model:

    qwen2.5-coder:7b
