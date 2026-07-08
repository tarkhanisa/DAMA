from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA dashboard smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Dashboard Project {uuid4().hex[:8]}"

    print("Creating dashboard test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Dashboard smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating dashboard test content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Dashboard Test Asset",
            "body": "Dashboard test asset body.",
            "status": "draft",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    print("Content asset created.")

    print("Checking GET /dashboard/summary...")
    summary_response = client.get("/dashboard/summary")
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()

    assert "system" in summary
    assert "projects" in summary
    assert "content_assets" in summary
    assert "exports" in summary
    assert "readiness" in summary

    assert summary["projects"]["total"] >= 1
    assert summary["content_assets"]["total"] >= 1
    assert summary["readiness"]["dashboard_ready"] is True
    assert summary["readiness"]["workflow_ready"] is True
    assert isinstance(summary["projects"]["recent"], list)
    assert isinstance(summary["content_assets"]["recent"], list)

    print("GET /dashboard/summary OK.")
    print("DAMA dashboard smoke test passed.")


if __name__ == "__main__":
    main()
