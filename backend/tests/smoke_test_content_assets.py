from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA content asset smoke test started.")

    client = TestClient(app)

    unique_name = f"DAMA Content Asset Project {uuid4().hex[:8]}"

    print("Creating test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": unique_name,
            "project_type": "content_campaign",
            "description": "Project for content asset smoke test.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Test project created.")

    print("Checking POST /content-assets...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "DAMA Test Blog Post",
            "body": "This is a persisted DAMA content asset.",
            "source": "manual",
            "metadata": {
                "test": True,
            },
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    asset = asset_response.json()
    assert asset["project_id"] == project_id
    assert asset["content_type"] == "blog_post"
    assert asset["status"] == "draft"
    asset_id = asset["id"]
    print("POST /content-assets OK.")

    print("Checking GET /content-assets/{asset_id}...")
    get_response = client.get(f"/content-assets/{asset_id}")
    assert get_response.status_code == 200, get_response.text
    loaded_asset = get_response.json()
    assert loaded_asset["id"] == asset_id
    assert loaded_asset["title"] == "DAMA Test Blog Post"
    print("GET /content-assets/{asset_id} OK.")

    print("Checking GET /content-assets...")
    list_response = client.get("/content-assets")
    assert list_response.status_code == 200, list_response.text
    assets = list_response.json()["content_assets"]
    assert any(item["id"] == asset_id for item in assets)
    print("GET /content-assets OK.")

    print("Checking GET /content-assets by project_id...")
    project_assets_response = client.get(f"/content-assets?project_id={project_id}")
    assert project_assets_response.status_code == 200, project_assets_response.text
    project_assets = project_assets_response.json()["content_assets"]
    assert any(item["id"] == asset_id for item in project_assets)
    print("GET /content-assets by project_id OK.")

    print("Checking PATCH /content-assets/{asset_id}/status...")
    status_response = client.patch(
        f"/content-assets/{asset_id}/status",
        json={
            "status": "review",
        },
    )
    assert status_response.status_code == 200, status_response.text
    updated_asset = status_response.json()
    assert updated_asset["status"] == "review"
    print("PATCH /content-assets/{asset_id}/status OK.")

    print("Checking invalid content asset project...")
    invalid_project_response = client.post(
        "/content-assets",
        json={
            "project_id": "missing-project-id",
            "content_type": "blog_post",
            "title": "Invalid Asset",
            "body": "Invalid asset body.",
        },
    )
    assert invalid_project_response.status_code == 404
    print("Invalid content asset project check OK.")

    print("Checking invalid content asset status...")
    invalid_status_response = client.patch(
        f"/content-assets/{asset_id}/status",
        json={
            "status": "fake_status",
        },
    )
    assert invalid_status_response.status_code == 400
    print("Invalid content asset status check OK.")

    print("DAMA content asset smoke test passed.")


if __name__ == "__main__":
    main()
