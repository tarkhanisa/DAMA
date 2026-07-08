from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA project persistence smoke test started.")

    client = TestClient(app)

    unique_name = f"DAMA Test Project {uuid4().hex[:8]}"

    print("Checking POST /projects...")
    create_response = client.post(
        "/projects",
        json={
            "name": unique_name,
            "project_type": "content_campaign",
            "description": "Persistent project smoke test.",
        },
    )
    assert create_response.status_code == 201, create_response.text

    created_project = create_response.json()
    assert created_project["name"] == unique_name
    assert created_project["project_type"] == "content_campaign"
    assert created_project["status"] == "draft"
    assert created_project["id"]

    project_id = created_project["id"]
    print("POST /projects OK.")

    print("Checking GET /projects/{project_id}...")
    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == 200, get_response.text
    loaded_project = get_response.json()
    assert loaded_project["id"] == project_id
    assert loaded_project["name"] == unique_name
    print("GET /projects/{project_id} OK.")

    print("Checking GET /projects...")
    list_response = client.get("/projects")
    assert list_response.status_code == 200, list_response.text
    projects = list_response.json()["projects"]
    assert any(project["id"] == project_id for project in projects)
    print("GET /projects OK.")

    print("Checking missing GET /projects/{project_id}...")
    missing_response = client.get("/projects/missing-project-id")
    assert missing_response.status_code == 404
    print("Missing project check OK.")

    print("Checking invalid POST /projects...")
    invalid_response = client.post(
        "/projects",
        json={
            "name": "Invalid Project",
            "project_type": "fake_type",
        },
    )
    assert invalid_response.status_code == 400
    print("Invalid project creation check OK.")

    print("DAMA project persistence smoke test passed.")


if __name__ == "__main__":
    main()
