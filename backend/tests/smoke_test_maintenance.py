from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA maintenance smoke test started.")

    client = TestClient(app)

    project_name = f"DAMA Maintenance Project {uuid4().hex[:8]}"

    print("Creating maintenance test project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "description": "Maintenance smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating maintenance test content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": "Maintenance Test Asset",
            "body": "Maintenance test asset body.",
            "status": "draft",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    print("Content asset created.")

    print("Checking GET /maintenance/status...")
    status_response = client.get("/maintenance/status")
    assert status_response.status_code == 200, status_response.text
    status = status_response.json()

    assert status["maintenance_ready"] is True
    assert status["database"]["exists"] is True
    assert status["database"]["tables"]["projects"] >= 1
    assert status["database"]["tables"]["content_assets"] >= 1
    assert "exports" in status
    assert "backups" in status
    print("GET /maintenance/status OK.")

    print("Checking POST /maintenance/database/backup...")
    backup_response = client.post("/maintenance/database/backup")
    assert backup_response.status_code == 200, backup_response.text
    backup = backup_response.json()

    assert backup["backup_created"] is True
    assert Path(backup["backup_path"]).exists()
    assert backup["size_bytes"] > 0
    print("POST /maintenance/database/backup OK.")

    print("Checking standardized 404 error shape...")
    missing_response = client.get("/projects/missing-project-id")
    assert missing_response.status_code == 404
    missing_error = missing_response.json()["error"]
    assert missing_error["type"] == "http_error"
    assert missing_error["status_code"] == 404
    assert missing_error["path"] == "/projects/missing-project-id"
    print("Standardized 404 error shape OK.")

    print("Checking standardized validation error shape...")
    validation_response = client.post(
        "/projects",
        json={
            "project_type": "content_campaign",
        },
    )
    assert validation_response.status_code == 422
    validation_error = validation_response.json()["error"]
    assert validation_error["type"] == "validation_error"
    assert validation_error["status_code"] == 422
    assert validation_error["path"] == "/projects"
    assert validation_error["details"]
    print("Standardized validation error shape OK.")

    print("DAMA maintenance smoke test passed.")


if __name__ == "__main__":
    main()
