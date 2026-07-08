from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from src.main import app


def main() -> None:
    print("DAMA search smoke test started.")

    client = TestClient(app)

    unique = uuid4().hex[:8]
    project_name = f"DAMA Search Project {unique}"
    asset_title = f"DAMA Search Asset {unique}"

    print("Creating searchable project...")
    project_response = client.post(
        "/projects",
        json={
            "name": project_name,
            "project_type": "content_campaign",
            "language": "en",
            "description": "Search smoke test project.",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]
    print("Project created.")

    print("Creating searchable content asset...")
    asset_response = client.post(
        "/content-assets",
        json={
            "project_id": project_id,
            "content_type": "blog_post",
            "title": asset_title,
            "body": "Search smoke test asset body.",
            "status": "review",
            "source": "manual",
        },
    )
    assert asset_response.status_code == 201, asset_response.text
    asset = asset_response.json()
    print("Content asset created.")

    print("Checking GET /search/projects by query...")
    project_search_response = client.get(
        "/search/projects",
        params={
            "query": unique,
            "limit": 10,
        },
    )
    assert project_search_response.status_code == 200, project_search_response.text
    project_search = project_search_response.json()
    assert project_search["total"] >= 1
    assert any(item["id"] == project_id for item in project_search["items"])
    print("Project query search OK.")

    print("Checking GET /search/projects by filters...")
    project_filter_response = client.get(
        "/search/projects",
        params={
            "project_type": "content_campaign",
            "language": "en",
            "status": "draft",
            "limit": 10,
        },
    )
    assert project_filter_response.status_code == 200, project_filter_response.text
    project_filter = project_filter_response.json()
    assert project_filter["limit"] == 10
    assert project_filter["offset"] == 0
    print("Project filter search OK.")

    print("Checking GET /search/content-assets by query...")
    asset_search_response = client.get(
        "/search/content-assets",
        params={
            "query": unique,
            "project_id": project_id,
        },
    )
    assert asset_search_response.status_code == 200, asset_search_response.text
    asset_search = asset_search_response.json()
    assert asset_search["total"] >= 1
    assert any(item["id"] == asset["id"] for item in asset_search["items"])
    print("Content asset query search OK.")

    print("Checking GET /search/content-assets by filters...")
    asset_filter_response = client.get(
        "/search/content-assets",
        params={
            "project_id": project_id,
            "content_type": "blog_post",
            "status": "review",
            "source": "manual",
        },
    )
    assert asset_filter_response.status_code == 200, asset_filter_response.text
    asset_filter = asset_filter_response.json()
    assert asset_filter["total"] >= 1
    assert any(item["id"] == asset["id"] for item in asset_filter["items"])
    print("Content asset filter search OK.")

    print("DAMA search smoke test passed.")


if __name__ == "__main__":
    main()
