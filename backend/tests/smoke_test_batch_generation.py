from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA batch generation smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Batch Generation {uuid4().hex[:8]}"

    print("Creating batch generation project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Batch generation smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]
    print("Project created.")

    print("Checking dry-run batch generation...")
    dry_run_response = client.post(
        f"/workflows/projects/{project_id}/batch-generate",
        json={
            "model": "dry-run-model",
            "topic": "DAMA batch generation dry run",
            "dry_run": True,
            "max_outputs": 2,
        },
    )
    assert dry_run_response.status_code == 200, dry_run_response.text
    dry_run = dry_run_response.json()
    assert dry_run["project_id"] == project_id
    assert dry_run["dry_run"] is True
    assert dry_run["planned_count"] == 2
    assert dry_run["generated_count"] == 0
    assert len(dry_run["planned_outputs"]) == 2
    assert dry_run["saved_content_assets"] == []
    print("Dry-run batch generation OK.")

    print("Checking dry-run content type filtering...")
    filtered_response = client.post(
        f"/workflows/projects/{project_id}/batch-generate",
        json={
            "model": "dry-run-model",
            "topic": "DAMA batch generation filtered dry run",
            "dry_run": True,
            "content_types": ["blog_post"],
        },
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered = filtered_response.json()
    assert filtered["planned_count"] == 1
    assert filtered["planned_outputs"][0]["content_type"] == "blog_post"
    print("Dry-run content type filtering OK.")

    print("Checking dry-run unmatched content type...")
    unmatched_response = client.post(
        f"/workflows/projects/{project_id}/batch-generate",
        json={
            "model": "dry-run-model",
            "topic": "DAMA unmatched dry run",
            "dry_run": True,
            "content_types": ["unknown_type"],
        },
    )
    assert unmatched_response.status_code == 400
    print("Unmatched content type check OK.")

    print("Checking missing project...")
    missing_response = client.post(
        "/workflows/projects/missing-project-id/batch-generate",
        json={
            "model": "dry-run-model",
            "dry_run": True,
        },
    )
    assert missing_response.status_code == 404
    print("Missing project check OK.")

    print("DAMA batch generation smoke test passed.")


if __name__ == "__main__":
    main()
