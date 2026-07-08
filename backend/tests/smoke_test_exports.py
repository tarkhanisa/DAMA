from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA export smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Export Project {uuid4().hex[:8]}"

    print("Creating export test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Export smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating export test content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Export Test Asset",
            "body": "This is the body of the export test asset.",
            "status": "approved",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    asset = asset_response.json()
    asset_id = asset["id"]
    print("Content asset created.")

    print("Checking POST /exports/content-assets/{asset_id}/markdown...")
    asset_export_response = client.post(f"/exports/content-assets/{asset_id}/markdown")
    assert asset_export_response.status_code == 200, asset_export_response.text
    asset_export = asset_export_response.json()
    assert asset_export["export_type"] == "content_asset_markdown"
    assert "Export Test Asset" in asset_export["content"]
    assert "This is the body of the export test asset." in asset_export["content"]
    assert Path(asset_export["file_path"]).exists()
    print("Content asset export OK.")

    print("Checking POST /exports/projects/{project_id}/bundle...")
    project_export_response = client.post(f"/exports/projects/{project_id}/bundle")
    assert project_export_response.status_code == 200, project_export_response.text
    project_export = project_export_response.json()
    assert project_export["export_type"] == "project_markdown_bundle"
    assert project_name in project_export["content"]
    assert "Export Test Asset" in project_export["content"]
    assert Path(project_export["file_path"]).exists()
    print("Project bundle export OK.")

    print("Checking missing content asset export...")
    missing_asset_response = client.post("/exports/content-assets/missing-asset/markdown")
    assert missing_asset_response.status_code == 404
    print("Missing content asset export check OK.")

    print("Checking missing project export...")
    missing_project_response = client.post("/exports/projects/missing-project/bundle")
    assert missing_project_response.status_code == 404
    print("Missing project export check OK.")

    print("DAMA export smoke test passed.")


if __name__ == "__main__":
    main()
