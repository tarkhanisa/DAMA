from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA workflow automation smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Workflow Automation {uuid4().hex[:8]}"

    print("Creating workflow automation project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Workflow automation smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Checking GET /workflows/projects/{project_id}/output-plan...")
    plan_response = client.get(
        f"/workflows/projects/{project_id}/output-plan",
        params={
            "topic": "DAMA workflow automation",
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    plan = plan_response.json()
    assert plan["project_id"] == project_id
    assert plan["planned_outputs"]
    assert any(item["content_type"] == "blog_post" for item in plan["planned_outputs"])
    print("Output plan OK.")

    print("Checking POST /workflows/projects/{project_id}/draft-assets...")
    draft_response = client.post(
        f"/workflows/projects/{project_id}/draft-assets",
        json={
            "topic": "DAMA workflow automation",
            "title_prefix": "Workflow Automation",
        },
    )
    assert draft_response.status_code == 200, draft_response.text
    draft_data = draft_response.json()
    created_assets = draft_data["created_assets"]
    assert created_assets
    assert all(asset["project_id"] == project_id for asset in created_assets)
    print("Draft assets OK.")

    print("Checking project summary after draft assets...")
    summary_response = client.get(f"/projects/{project_id}/summary")
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["total_assets"] >= len(created_assets)
    assert summary["assets_by_status"]["draft"] >= len(created_assets)
    print("Project summary after draft assets OK.")

    print("Checking missing workflow project...")
    missing_response = client.get("/workflows/projects/missing-project-id/output-plan")
    assert missing_response.status_code == 404
    print("Missing workflow project check OK.")

    print("DAMA workflow automation smoke test passed.")


if __name__ == "__main__":
    main()
