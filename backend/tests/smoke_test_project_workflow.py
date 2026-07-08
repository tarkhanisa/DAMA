from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA project workflow smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Workflow Project {uuid4().hex[:8]}"

    print("Creating workflow project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Project workflow smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Workflow project created.")

    print("Creating draft content asset...")
    draft_asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Workflow Draft Asset",
            "body": "Workflow draft asset body.",
            "status": "draft",
        },
    )
    assert draft_asset_response.status_code == 201, draft_asset_response.text
    draft_asset_id = draft_asset_response.json()["id"]
    print("Draft content asset created.")

    print("Creating review content asset...")
    review_asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "social_caption",
            "title": "Workflow Review Asset",
            "body": "Workflow review asset body.",
            "status": "review",
        },
    )
    assert review_asset_response.status_code == 201, review_asset_response.text
    review_asset_id = review_asset_response.json()["id"]
    print("Review content asset created.")

    print("Checking GET /projects/{project_id}/content-assets...")
    project_assets_response = client.get(f"/projects/{project_id}/content-assets")
    assert project_assets_response.status_code == 200, project_assets_response.text
    project_assets = project_assets_response.json()["content_assets"]
    asset_ids = {asset["id"] for asset in project_assets}
    assert draft_asset_id in asset_ids
    assert review_asset_id in asset_ids
    print("GET /projects/{project_id}/content-assets OK.")

    print("Checking GET /projects/{project_id}/summary...")
    summary_response = client.get(f"/projects/{project_id}/summary")
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["project"]["id"] == project_id
    assert summary["total_assets"] >= 2
    assert summary["assets_by_status"]["draft"] >= 1
    assert summary["assets_by_status"]["review"] >= 1
    assert summary["assets_by_content_type"]["blog_post"] >= 1
    assert summary["assets_by_content_type"]["social_caption"] >= 1
    print("GET /projects/{project_id}/summary OK.")

    print("Checking PATCH /projects/{project_id}/status...")
    status_response = client.patch(
        f"/projects/{project_id}/status",
        json={
            "status": "active",
        },
    )
    assert status_response.status_code == 200, status_response.text
    updated_project = status_response.json()
    assert updated_project["status"] == "active"
    print("PATCH /projects/{project_id}/status OK.")

    print("Checking invalid project status...")
    invalid_status_response = client.patch(
        f"/projects/{project_id}/status",
        json={
            "status": "fake_status",
        },
    )
    assert invalid_status_response.status_code == 400
    print("Invalid project status check OK.")

    print("Checking missing project summary...")
    missing_summary_response = client.get("/projects/missing-project-id/summary")
    assert missing_summary_response.status_code == 404
    print("Missing project summary check OK.")

    print("DAMA project workflow smoke test passed.")


if __name__ == "__main__":
    main()
