from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


def patch_file(path: str, patcher) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    new_text = patcher(text)
    target.write_text(new_text, encoding="utf-8")
    print(f"Patched {path}")


write_file(
    "backend/src/services/search_service.py",
    r'''
from __future__ import annotations

import json
from typing import Any

from src.database.sqlite_database import get_connection, initialize_database


class SearchServiceError(RuntimeError):
    pass


class SearchService:
    @classmethod
    def search_projects(
        cls,
        *,
        query: str | None = None,
        status: str | None = None,
        project_type: str | None = None,
        language: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        initialize_database()

        conditions: list[str] = []
        params: list[Any] = []

        if query and query.strip():
            like_query = f"%{query.strip().lower()}%"
            conditions.append(
                "(LOWER(name) LIKE ? OR LOWER(slug) LIKE ? OR LOWER(description) LIKE ?)"
            )
            params.extend([like_query, like_query, like_query])

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip())

        if project_type and project_type.strip():
            conditions.append("project_type = ?")
            params.append(project_type.strip())

        if language and language.strip():
            conditions.append("language = ?")
            params.append(language.strip())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        safe_limit = cls._normalize_limit(limit)
        safe_offset = cls._normalize_offset(offset)

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM projects {where_clause}",
                params,
            ).fetchone()["count"]

            rows = connection.execute(
                f"""
                SELECT
                    id,
                    name,
                    slug,
                    project_type,
                    language,
                    description,
                    status,
                    content_types,
                    created_at,
                    updated_at
                FROM projects
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, safe_limit, safe_offset],
            ).fetchall()

        return {
            "total": total,
            "limit": safe_limit,
            "offset": safe_offset,
            "items": [cls._project_row_to_dict(row) for row in rows],
        }

    @classmethod
    def search_content_assets(
        cls,
        *,
        query: str | None = None,
        project_id: str | None = None,
        status: str | None = None,
        content_type: str | None = None,
        source: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        initialize_database()

        conditions: list[str] = []
        params: list[Any] = []

        if query and query.strip():
            like_query = f"%{query.strip().lower()}%"
            conditions.append("(LOWER(title) LIKE ? OR LOWER(body) LIKE ?)")
            params.extend([like_query, like_query])

        if project_id and project_id.strip():
            conditions.append("project_id = ?")
            params.append(project_id.strip())

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip())

        if content_type and content_type.strip():
            conditions.append("content_type = ?")
            params.append(content_type.strip())

        if source and source.strip():
            conditions.append("source = ?")
            params.append(source.strip())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        safe_limit = cls._normalize_limit(limit)
        safe_offset = cls._normalize_offset(offset)

        with get_connection() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM content_assets {where_clause}",
                params,
            ).fetchone()["count"]

            rows = connection.execute(
                f"""
                SELECT
                    id,
                    project_id,
                    content_type,
                    title,
                    body,
                    status,
                    source,
                    metadata,
                    created_at,
                    updated_at
                FROM content_assets
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [*params, safe_limit, safe_offset],
            ).fetchall()

        return {
            "total": total,
            "limit": safe_limit,
            "offset": safe_offset,
            "items": [cls._asset_row_to_dict(row) for row in rows],
        }

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        try:
            value = int(limit)
        except (TypeError, ValueError):
            value = 20

        return max(1, min(value, 100))

    @staticmethod
    def _normalize_offset(offset: int) -> int:
        try:
            value = int(offset)
        except (TypeError, ValueError):
            value = 0

        return max(0, value)

    @staticmethod
    def _loads_json(value: Any, fallback: Any) -> Any:
        if value is None:
            return fallback

        if isinstance(value, (list, dict)):
            return value

        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return fallback

    @classmethod
    def _project_row_to_dict(cls, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "project_type": row["project_type"],
            "language": row["language"],
            "description": row["description"],
            "status": row["status"],
            "content_types": cls._loads_json(row["content_types"], []),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @classmethod
    def _asset_row_to_dict(cls, row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "content_type": row["content_type"],
            "title": row["title"],
            "body": row["body"],
            "status": row["status"],
            "source": row["source"],
            "metadata": cls._loads_json(row["metadata"], {}),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    ''',
)


write_file(
    "backend/src/api/search.py",
    r'''
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from src.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"])


@router.get("/projects")
def search_projects(
    query: str | None = None,
    status: str | None = None,
    project_type: str | None = None,
    language: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return SearchService.search_projects(
        query=query,
        status=status,
        project_type=project_type,
        language=language,
        limit=limit,
        offset=offset,
    )


@router.get("/content-assets")
def search_content_assets(
    query: str | None = None,
    project_id: str | None = None,
    status: str | None = None,
    content_type: str | None = None,
    source: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return SearchService.search_content_assets(
        query=query,
        project_id=project_id,
        status=status,
        content_type=content_type,
        source=source,
        limit=limit,
        offset=offset,
    )
    ''',
)


def patch_main(text: str) -> str:
    if "from src.api.search import router as search_router" not in text:
        marker = "from src.api.projects import router as projects_router"
        text = text.replace(marker, marker + "\nfrom src.api.search import router as search_router")

    if "app.include_router(search_router)" not in text:
        marker = "app.include_router(projects_router)"
        text = text.replace(marker, marker + "\napp.include_router(search_router)")

    return text


patch_file("backend/src/main.py", patch_main)


def patch_api_init(text: str) -> str:
    if "search_router" not in text:
        text = text.rstrip() + "\nfrom .search import router as search_router\n"
    return text


patch_file("backend/src/api/__init__.py", patch_api_init)


write_file(
    "backend/tests/smoke_test_search.py",
    r'''
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
    ''',
)


def patch_backend_check(text: str) -> str:
    if "smoke_test_search.py" in text:
        return text

    marker = '".\\backend\\tests\\smoke_test_developer.py"'
    replacement = marker + ',\n    ".\\backend\\tests\\smoke_test_search.py"'
    return text.replace(marker, replacement)


patch_file("scripts/backend-check.ps1", patch_backend_check)


write_file(
    "frontend/src/components/search-filter-card.tsx",
    r'''
type SearchFilterCardProps = {
  title: string;
  children: React.ReactNode;
};

export function SearchFilterCard({ title, children }: SearchFilterCardProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">Search</p>
        <h2>{title}</h2>
      </div>

      <form className="filter-form" method="get">
        {children}
        <button type="submit">Apply filters</button>
      </form>
    </section>
  );
}
    ''',
)


write_file(
    "frontend/src/components/asset-body-preview.tsx",
    r'''
type AssetBodyPreviewProps = {
  body?: string;
};

export function AssetBodyPreview({ body }: AssetBodyPreviewProps) {
  const normalized = String(body ?? "").trim();

  if (!normalized) {
    return <p className="empty-state">No body content.</p>;
  }

  return <pre className="asset-body-preview">{normalized}</pre>;
}
    ''',
)


write_file(
    "frontend/src/lib/types.ts",
    r'''
export type DamaError = {
  error: {
    type: "http_error" | "validation_error";
    status_code: number;
    message: string;
    path: string;
    details?: unknown[];
  };
};

export type Project = {
  id: string;
  name: string;
  slug?: string;
  project_type: string;
  language?: string;
  description?: string;
  status: string;
  content_types?: string[];
  created_at?: string;
  updated_at?: string;
};

export type CreateProjectInput = {
  name: string;
  project_type: string;
  language?: string;
  description?: string;
  content_types?: string[];
};

export type ContentAsset = {
  id: string;
  project_id: string;
  content_type: string;
  title: string;
  body?: string;
  status: string;
  source: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type CreateContentAssetInput = {
  project_id: string;
  content_type: string;
  title: string;
  body: string;
  status?: string;
  source?: string;
  metadata?: Record<string, unknown>;
};

export type SearchResponse<T> = {
  total: number;
  limit: number;
  offset: number;
  items: T[];
};

export type ProjectSearchParams = {
  query?: string;
  status?: string;
  project_type?: string;
  language?: string;
  limit?: number;
  offset?: number;
};

export type ContentAssetSearchParams = {
  query?: string;
  project_id?: string;
  status?: string;
  content_type?: string;
  source?: string;
  limit?: number;
  offset?: number;
};

export type ProjectSummary = {
  project: Project;
  total_assets: number;
  assets_by_status: Record<string, number>;
  assets_by_content_type: Record<string, number>;
  recent_assets: ContentAsset[];
};

export type ProjectContentAssetsResponse = {
  project_id: string;
  content_assets: ContentAsset[];
};

export type PlannedOutput = {
  order: number;
  project_id: string;
  content_type: string;
  title: string;
  workflow_stage: string;
  recommended_status: string;
  generation_topic: string;
};

export type OutputPlanResponse = {
  project_id: string;
  planned_outputs: PlannedOutput[];
};

export type BatchGenerateDryRunInput = {
  model: string;
  topic?: string;
  content_types?: string[];
  max_outputs?: number;
  dry_run: true;
};

export type BatchGenerateResponse = {
  project_id: string;
  dry_run: boolean;
  planned_count: number;
  generated_count: number;
  planned_outputs: PlannedOutput[];
  saved_content_assets: ContentAsset[];
};

export type MaintenanceStatus = {
  database: {
    path: string;
    exists: boolean;
    size_bytes: number;
    tables: Record<string, number>;
  };
  exports: {
    path: string;
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    recent: Array<{
      file_name: string;
      file_path: string;
      size_bytes: number;
    }>;
  };
  backups: {
    path: string;
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    recent: Array<{
      file_name: string;
      file_path: string;
      size_bytes: number;
    }>;
  };
  maintenance_ready: boolean;
  generated_at: string;
};

export type DashboardSummary = {
  system: Record<string, unknown>;
  projects: {
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    recent: Project[];
  };
  content_assets: {
    total: number;
    by_status: Record<string, number>;
    by_content_type: Record<string, number>;
    by_source: Record<string, number>;
    recent: ContentAsset[];
  };
  exports: {
    total_markdown_files: number;
    export_root: string;
    recent: Array<{
      file_name?: string;
      file_path?: string;
      size_bytes?: number;
    }>;
  };
  readiness: {
    has_projects: boolean;
    has_content_assets: boolean;
    has_exports: boolean;
    dashboard_ready: boolean;
    workflow_ready: boolean;
    export_ready: boolean;
  };
};

export type FrontendContract = {
  name: string;
  version: string;
  backend_base_url: string;
  interactive_docs: string;
  openapi_json: string;
  recommended_frontend_sections: Array<{
    key: string;
    title: string;
    primary_endpoints: string[];
  }>;
  endpoint_count: number;
};
    ''',
)


write_file(
    "frontend/src/lib/api-client.ts",
    r'''
import type {
  BatchGenerateDryRunInput,
  BatchGenerateResponse,
  ContentAsset,
  ContentAssetSearchParams,
  CreateContentAssetInput,
  CreateProjectInput,
  DashboardSummary,
  FrontendContract,
  MaintenanceStatus,
  OutputPlanResponse,
  Project,
  ProjectContentAssetsResponse,
  ProjectSearchParams,
  ProjectSummary,
  SearchResponse
} from "./types";

export const DAMA_API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${DAMA_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(JSON.stringify(data));
  }

  return data as T;
}

function normalizeListResponse<T>(data: unknown, possibleKeys: string[]): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }

  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;

    for (const key of possibleKeys) {
      const value = record[key];

      if (Array.isArray(value)) {
        return value as T[];
      }
    }
  }

  return [];
}

function toQueryString(params: Record<string, string | number | undefined>): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && String(value).trim() !== "") {
      searchParams.set(key, String(value));
    }
  }

  const queryString = searchParams.toString();

  return queryString ? `?${queryString}` : "";
}

export const damaApi = {
  dashboardSummary(): Promise<DashboardSummary> {
    return requestJson<DashboardSummary>("/dashboard/summary");
  },

  frontendContract(): Promise<FrontendContract> {
    return requestJson<FrontendContract>("/developer/frontend-contract");
  },

  endpointMap(): Promise<unknown> {
    return requestJson<unknown>("/developer/endpoint-map");
  },

  runbook(): Promise<unknown> {
    return requestJson<unknown>("/developer/runbook");
  },

  maintenanceStatus(): Promise<MaintenanceStatus> {
    return requestJson<MaintenanceStatus>("/maintenance/status");
  },

  async projects(): Promise<Project[]> {
    const data = await requestJson<unknown>("/projects");
    return normalizeListResponse<Project>(data, ["projects", "items", "results"]);
  },

  searchProjects(params: ProjectSearchParams): Promise<SearchResponse<Project>> {
    return requestJson<SearchResponse<Project>>(
      `/search/projects${toQueryString(params)}`
    );
  },

  createProject(input: CreateProjectInput): Promise<Project> {
    return requestJson<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },

  project(projectId: string): Promise<Project> {
    return requestJson<Project>(`/projects/${projectId}`);
  },

  projectSummary(projectId: string): Promise<ProjectSummary> {
    return requestJson<ProjectSummary>(`/projects/${projectId}/summary`);
  },

  projectContentAssets(projectId: string): Promise<ProjectContentAssetsResponse> {
    return requestJson<ProjectContentAssetsResponse>(
      `/projects/${projectId}/content-assets`
    );
  },

  projectOutputPlan(projectId: string): Promise<OutputPlanResponse> {
    return requestJson<OutputPlanResponse>(
      `/workflows/projects/${projectId}/output-plan`
    );
  },

  batchGenerateDryRun(
    projectId: string,
    input: BatchGenerateDryRunInput
  ): Promise<BatchGenerateResponse> {
    return requestJson<BatchGenerateResponse>(
      `/workflows/projects/${projectId}/batch-generate`,
      {
        method: "POST",
        body: JSON.stringify(input)
      }
    );
  },

  async contentAssets(): Promise<ContentAsset[]> {
    const data = await requestJson<unknown>("/content-assets");
    return normalizeListResponse<ContentAsset>(data, [
      "content_assets",
      "assets",
      "items",
      "results"
    ]);
  },

  searchContentAssets(
    params: ContentAssetSearchParams
  ): Promise<SearchResponse<ContentAsset>> {
    return requestJson<SearchResponse<ContentAsset>>(
      `/search/content-assets${toQueryString(params)}`
    );
  },

  contentAsset(assetId: string): Promise<ContentAsset> {
    return requestJson<ContentAsset>(`/content-assets/${assetId}`);
  },

  createContentAsset(input: CreateContentAssetInput): Promise<ContentAsset> {
    return requestJson<ContentAsset>("/content-assets", {
      method: "POST",
      body: JSON.stringify(input)
    });
  }
};
    ''',
)


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/content-assets", label: "Content Assets" },
  { href: "/workflows", label: "Workflows" },
  { href: "/search", label: "Search" },
  { href: "/exports", label: "Exports" },
  { href: "/maintenance", label: "Maintenance" }
];

export function AppNav() {
  return (
    <nav className="app-nav">
      <a className="brand-link" href="/">
        DAMA
      </a>

      <div>
        {navItems.map((item) => (
          <a key={item.href} href={item.href}>
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
    ''',
)


write_file(
    "frontend/src/app/search/page.tsx",
    r'''
import { ActionCard } from "../../components/action-card";
import { PageHeader } from "../../components/page-header";

export default function SearchPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Search"
        title="Search and filters"
        lead="Find projects and content assets using backend search endpoints."
      />

      <section className="action-grid">
        <ActionCard
          title="Search Projects"
          description="Search by name, slug, description, status, type, and language."
          href="/search/projects"
          label="Open"
        />
        <ActionCard
          title="Search Content Assets"
          description="Search by title, body, project, status, content type, and source."
          href="/search/content-assets"
          label="Open"
        />
        <ActionCard
          title="Backend Search API"
          description="Inspect raw search endpoints in Swagger."
          href="http://127.0.0.1:8000/docs"
          label="Docs"
        />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/search/projects/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../../components/data-table";
import { PageHeader } from "../../../components/page-header";
import { SearchFilterCard } from "../../../components/search-filter-card";
import { StatCard } from "../../../components/stat-card";
import { damaApi } from "../../../lib/api-client";
import type { Project, SearchResponse } from "../../../lib/types";

type SearchParams = Record<string, string | string[] | undefined>;

type SearchProjectsPageProps = {
  searchParams?: SearchParams | Promise<SearchParams>;
};

async function resolveSearchParams(
  searchParams: SearchProjectsPageProps["searchParams"]
): Promise<SearchParams> {
  return searchParams ? await searchParams : {};
}

function getParam(params: SearchParams, key: string): string {
  const value = params[key];
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

async function loadResults(params: SearchParams): Promise<SearchResponse<Project>> {
  try {
    return await damaApi.searchProjects({
      query: getParam(params, "query"),
      status: getParam(params, "status"),
      project_type: getParam(params, "project_type"),
      language: getParam(params, "language"),
      limit: Number(getParam(params, "limit") || 20),
      offset: Number(getParam(params, "offset") || 0)
    });
  } catch {
    return {
      total: 0,
      limit: 20,
      offset: 0,
      items: []
    };
  }
}

export default async function SearchProjectsPage({
  searchParams
}: SearchProjectsPageProps) {
  const params = await resolveSearchParams(searchParams);
  const results = await loadResults(params);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Search Projects"
        title="Project search"
        lead="Search and filter DAMA project records."
      />

      <SearchFilterCard title="Project filters">
        <label>
          Query
          <input name="query" defaultValue={getParam(params, "query")} placeholder="Project name or description" />
        </label>

        <label>
          Status
          <input name="status" defaultValue={getParam(params, "status")} placeholder="draft, active, review..." />
        </label>

        <label>
          Project type
          <input name="project_type" defaultValue={getParam(params, "project_type")} placeholder="content_campaign" />
        </label>

        <label>
          Language
          <input name="language" defaultValue={getParam(params, "language")} placeholder="en" />
        </label>

        <label>
          Limit
          <input name="limit" type="number" min="1" max="100" defaultValue={getParam(params, "limit") || "20"} />
        </label>
      </SearchFilterCard>

      <section className="stats-grid">
        <StatCard label="Results" value={results.total} helper="Total matching projects" />
        <StatCard label="Shown" value={results.items.length} helper="Loaded result rows" />
        <StatCard label="Limit" value={results.limit} helper="Current result limit" />
        <StatCard label="Offset" value={results.offset} helper="Current offset" />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Results</p>
          <h2>Projects</h2>
        </div>

        <DataTable<Project>
          emptyLabel="No matching projects found."
          items={results.items}
          columns={[
            {
              key: "name",
              label: "Name",
              render: (project) => (
                <a className="table-link" href={`/projects/${project.id}`}>
                  {project.name}
                </a>
              )
            },
            {
              key: "type",
              label: "Type",
              render: (project) => project.project_type
            },
            {
              key: "language",
              label: "Language",
              render: (project) => project.language ?? "—"
            },
            {
              key: "status",
              label: "Status",
              render: (project) => <StatusPill status={project.status} />
            }
          ]}
        />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/search/content-assets/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../../components/data-table";
import { PageHeader } from "../../../components/page-header";
import { SearchFilterCard } from "../../../components/search-filter-card";
import { StatCard } from "../../../components/stat-card";
import { damaApi } from "../../../lib/api-client";
import type { ContentAsset, SearchResponse } from "../../../lib/types";

type SearchParams = Record<string, string | string[] | undefined>;

type SearchContentAssetsPageProps = {
  searchParams?: SearchParams | Promise<SearchParams>;
};

async function resolveSearchParams(
  searchParams: SearchContentAssetsPageProps["searchParams"]
): Promise<SearchParams> {
  return searchParams ? await searchParams : {};
}

function getParam(params: SearchParams, key: string): string {
  const value = params[key];
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

async function loadResults(
  params: SearchParams
): Promise<SearchResponse<ContentAsset>> {
  try {
    return await damaApi.searchContentAssets({
      query: getParam(params, "query"),
      project_id: getParam(params, "project_id"),
      status: getParam(params, "status"),
      content_type: getParam(params, "content_type"),
      source: getParam(params, "source"),
      limit: Number(getParam(params, "limit") || 20),
      offset: Number(getParam(params, "offset") || 0)
    });
  } catch {
    return {
      total: 0,
      limit: 20,
      offset: 0,
      items: []
    };
  }
}

export default async function SearchContentAssetsPage({
  searchParams
}: SearchContentAssetsPageProps) {
  const params = await resolveSearchParams(searchParams);
  const results = await loadResults(params);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Search Content"
        title="Content asset search"
        lead="Search and filter DAMA content assets."
      />

      <SearchFilterCard title="Content asset filters">
        <label>
          Query
          <input name="query" defaultValue={getParam(params, "query")} placeholder="Title or body text" />
        </label>

        <label>
          Project ID
          <input name="project_id" defaultValue={getParam(params, "project_id")} placeholder="Optional project id" />
        </label>

        <label>
          Status
          <input name="status" defaultValue={getParam(params, "status")} placeholder="draft, review, approved..." />
        </label>

        <label>
          Content type
          <input name="content_type" defaultValue={getParam(params, "content_type")} placeholder="blog_post" />
        </label>

        <label>
          Source
          <input name="source" defaultValue={getParam(params, "source")} placeholder="manual, ai_generated" />
        </label>

        <label>
          Limit
          <input name="limit" type="number" min="1" max="100" defaultValue={getParam(params, "limit") || "20"} />
        </label>
      </SearchFilterCard>

      <section className="stats-grid">
        <StatCard label="Results" value={results.total} helper="Total matching assets" />
        <StatCard label="Shown" value={results.items.length} helper="Loaded result rows" />
        <StatCard label="Limit" value={results.limit} helper="Current result limit" />
        <StatCard label="Offset" value={results.offset} helper="Current offset" />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Results</p>
          <h2>Content assets</h2>
        </div>

        <DataTable<ContentAsset>
          emptyLabel="No matching content assets found."
          items={results.items}
          columns={[
            {
              key: "title",
              label: "Title",
              render: (asset) => (
                <a className="table-link" href={`/content-assets/${asset.id}`}>
                  {asset.title}
                </a>
              )
            },
            {
              key: "type",
              label: "Type",
              render: (asset) => asset.content_type
            },
            {
              key: "source",
              label: "Source",
              render: (asset) => asset.source
            },
            {
              key: "status",
              label: "Status",
              render: (asset) => <StatusPill status={asset.status} />
            }
          ]}
        />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/content-assets/[assetId]/page.tsx",
    r'''
import { AssetBodyPreview } from "../../../components/asset-body-preview";
import { ErrorPanel } from "../../../components/error-panel";
import { JsonPreview } from "../../../components/json-preview";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../../lib/api-client";
import type { ContentAsset } from "../../../lib/types";

type AssetDetailPageProps = {
  params: {
    assetId: string;
  } | Promise<{
    assetId: string;
  }>;
};

async function resolveParams(params: AssetDetailPageProps["params"]) {
  return await params;
}

async function loadAsset(assetId: string): Promise<ContentAsset | null> {
  try {
    return await damaApi.contentAsset(assetId);
  } catch {
    return null;
  }
}

export default async function AssetDetailPage({ params }: AssetDetailPageProps) {
  const resolvedParams = await resolveParams(params);
  const asset = await loadAsset(resolvedParams.assetId);

  if (!asset) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="Content Asset"
          title="Content asset not found"
          message="The selected content asset could not be loaded from the backend."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Content Asset"
        title={asset.title}
        lead="Inspect content asset metadata, body, project connection, and export endpoint."
      >
        <div className="actions">
          <a href={`/projects/${asset.project_id}`}>Open Project</a>
          <a href={`${DAMA_API_BASE_URL}/content-assets/${asset.id}`}>
            Raw Asset JSON
          </a>
          <a href={`${DAMA_API_BASE_URL}/exports/content-assets/${asset.id}/markdown`}>
            Markdown Export Endpoint
          </a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Status" value={asset.status} helper="Asset status" />
        <StatCard label="Source" value={asset.source} helper="Asset source" />
        <StatCard label="Type" value={asset.content_type} helper="Content type" />
        <StatCard label="Project" value="Linked" helper={asset.project_id} />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Body</p>
          <h2>Content body</h2>
        </div>

        <AssetBodyPreview body={asset.body} />
      </section>

      <JsonPreview title="Asset metadata" data={asset.metadata ?? {}} />
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/content-assets/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../components/data-table";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { damaApi } from "../../lib/api-client";
import type { ContentAsset } from "../../lib/types";

async function loadContentAssets(): Promise<ContentAsset[]> {
  try {
    return await damaApi.contentAssets();
  } catch {
    return [];
  }
}

export default async function ContentAssetsPage() {
  const assets = await loadContentAssets();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Content Assets"
        title="Content asset library"
        lead="Browse manual and AI-generated content assets stored inside DAMA."
      >
        <div className="actions">
          <a href="/content-assets/new">Create content asset</a>
          <a href="/search/content-assets">Search assets</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Assets" value={assets.length} helper="Total loaded assets" />
        <StatCard
          label="AI Generated"
          value={assets.filter((asset) => asset.source === "ai_generated").length}
          helper="Generated by AI workflows"
        />
        <StatCard
          label="Manual"
          value={assets.filter((asset) => asset.source === "manual").length}
          helper="Manual content records"
        />
        <StatCard
          label="Types"
          value={new Set(assets.map((asset) => asset.content_type)).size}
          helper="Unique content types"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Library</p>
          <h2>All content assets</h2>
        </div>

        <DataTable<ContentAsset>
          emptyLabel="No content assets found."
          items={assets}
          columns={[
            {
              key: "title",
              label: "Title",
              render: (asset) => (
                <a className="table-link" href={`/content-assets/${asset.id}`}>
                  {asset.title}
                </a>
              )
            },
            {
              key: "content_type",
              label: "Type",
              render: (asset) => asset.content_type
            },
            {
              key: "source",
              label: "Source",
              render: (asset) => asset.source
            },
            {
              key: "status",
              label: "Status",
              render: (asset) => <StatusPill status={asset.status} />
            }
          ]}
        />
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/projects/page.tsx",
    r'''
import { DataTable, StatusPill } from "../../components/data-table";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { damaApi } from "../../lib/api-client";
import type { Project } from "../../lib/types";

async function loadProjects(): Promise<Project[]> {
  try {
    return await damaApi.projects();
  } catch {
    return [];
  }
}

export default async function ProjectsPage() {
  const projects = await loadProjects();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Projects"
        title="Project workspace"
        lead="Browse DAMA projects and open project summaries for content workflow management."
      >
        <div className="actions">
          <a href="/projects/new">Create project</a>
          <a href="/search/projects">Search projects</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Projects" value={projects.length} helper="Loaded from backend" />
        <StatCard
          label="Active"
          value={projects.filter((project) => project.status === "active").length}
          helper="Active project records"
        />
        <StatCard
          label="Draft"
          value={projects.filter((project) => project.status === "draft").length}
          helper="Draft project records"
        />
        <StatCard
          label="Types"
          value={new Set(projects.map((project) => project.project_type)).size}
          helper="Unique project types"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Project List</p>
          <h2>All projects</h2>
        </div>

        <DataTable<Project>
          emptyLabel="No projects found."
          items={projects}
          columns={[
            {
              key: "name",
              label: "Name",
              render: (project) => (
                <a className="table-link" href={`/projects/${project.id}`}>
                  {project.name}
                </a>
              )
            },
            {
              key: "type",
              label: "Type",
              render: (project) => project.project_type
            },
            {
              key: "language",
              label: "Language",
              render: (project) => project.language ?? "—"
            },
            {
              key: "status",
              label: "Status",
              render: (project) => <StatusPill status={project.status} />
            }
          ]}
        />
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Release Pack N: search and asset detail */",
    r'''
/* Release Pack N: search and asset detail */

.filter-form {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-top: 20px;
  align-items: end;
}

.filter-form label {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-weight: 800;
}

.filter-form input,
.filter-form select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: white;
  color: var(--text);
}

.filter-form button {
  width: fit-content;
  padding: 12px 16px;
  border: 0;
  border-radius: 999px;
  background: var(--accent);
  color: white;
  font-weight: 900;
  cursor: pointer;
}

.asset-body-preview {
  margin-top: 18px;
  padding: 22px;
  white-space: pre-wrap;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface-strong);
  color: var(--text);
  line-height: 1.7;
}

@media (max-width: 980px) {
  .filter-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .filter-form {
    grid-template-columns: 1fr;
  }
}
    ''',
)


write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RequiredFiles = @(
    ".\frontend\README.md",
    ".\frontend\package.json",
    ".\frontend\next.config.mjs",
    ".\frontend\tsconfig.json",
    ".\frontend\src\app\layout.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\projects\page.tsx",
    ".\frontend\src\app\projects\new\page.tsx",
    ".\frontend\src\app\projects\[projectId]\page.tsx",
    ".\frontend\src\app\content-assets\page.tsx",
    ".\frontend\src\app\content-assets\new\page.tsx",
    ".\frontend\src\app\content-assets\[assetId]\page.tsx",
    ".\frontend\src\app\workflows\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\page.tsx",
    ".\frontend\src\app\workflows\[projectId]\dry-run\page.tsx",
    ".\frontend\src\app\search\page.tsx",
    ".\frontend\src\app\search\projects\page.tsx",
    ".\frontend\src\app\search\content-assets\page.tsx",
    ".\frontend\src\app\exports\page.tsx",
    ".\frontend\src\app\maintenance\page.tsx",
    ".\frontend\src\app\globals.css",
    ".\frontend\src\lib\api-client.ts",
    ".\frontend\src\lib\types.ts",
    ".\frontend\src\lib\formatters.ts",
    ".\frontend\src\components\app-nav.tsx",
    ".\frontend\src\components\search-filter-card.tsx",
    ".\frontend\src\components\asset-body-preview.tsx",
    ".\frontend\src\components\stat-card.tsx",
    ".\frontend\src\components\readiness-panel.tsx",
    ".\frontend\src\components\recent-list.tsx",
    ".\frontend\src\components\count-breakdown.tsx",
    ".\frontend\src\components\link-card.tsx",
    ".\frontend\src\components\data-table.tsx",
    ".\frontend\src\components\status-pill.tsx",
    ".\frontend\src\components\action-card.tsx",
    ".\frontend\src\components\json-preview.tsx",
    ".\frontend\src\components\page-header.tsx",
    ".\frontend\src\components\error-panel.tsx",
    ".\frontend\src\components\form-status.tsx",
    ".\frontend\src\components\create-project-form.tsx",
    ".\frontend\src\components\create-content-asset-form.tsx",
    ".\frontend\src\components\workflow-dry-run-form.tsx"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Frontend file is missing: $File"
    }
}

$ApiClient = Get-Content ".\frontend\src\lib\api-client.ts" -Raw
$Nav = Get-Content ".\frontend\src\components\app-nav.tsx" -Raw
$SearchProjects = Get-Content ".\frontend\src\app\search\projects\page.tsx" -Raw
$SearchAssets = Get-Content ".\frontend\src\app\search\content-assets\page.tsx" -Raw
$AssetDetail = Get-Content ".\frontend\src\app\content-assets\[assetId]\page.tsx" -Raw

if ($ApiClient -notmatch "searchProjects") {
    throw "API client does not expose searchProjects."
}

if ($ApiClient -notmatch "searchContentAssets") {
    throw "API client does not expose searchContentAssets."
}

if ($ApiClient -notmatch "contentAsset") {
    throw "API client does not expose contentAsset."
}

if ($Nav -notmatch "/search") {
    throw "Navigation does not include search."
}

if ($SearchProjects -notmatch "damaApi.searchProjects") {
    throw "Search projects page does not use searchProjects."
}

if ($SearchAssets -notmatch "damaApi.searchContentAssets") {
    throw "Search content assets page does not use searchContentAssets."
}

if ($AssetDetail -notmatch "Markdown Export Endpoint") {
    throw "Content asset detail page does not expose export endpoint."
}

if (Test-Path ".\frontend\node_modules") {
    Write-Host "node_modules found. Running frontend typecheck..."
    Push-Location ".\frontend"
    try {
        npm run typecheck
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend typecheck failed."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "node_modules not found. Skipping npm typecheck."
}

Write-Host "Frontend search and detail UI check passed."
    ''',
)


write_file(
    "docs/search-and-filters.md",
    r'''
# DAMA Search and Filters

Release Pack N adds search and filter support.

## Backend Endpoints

Search projects:

    GET /search/projects

Supported query fields:

- query
- status
- project_type
- language
- limit
- offset

Search content assets:

    GET /search/content-assets

Supported query fields:

- query
- project_id
- status
- content_type
- source
- limit
- offset

## Frontend Routes

    /search
    /search/projects
    /search/content-assets
    /content-assets/[assetId]

## Safety

Search endpoints are read-only.

The content asset detail page links to export endpoints but does not execute destructive actions.
    ''',
)


append_once(
    "docs/backend-api.md",
    "## Search API",
    r'''
## Search API

Release Pack N adds read-only search endpoints.

GET /search/projects

Filters:

- query
- status
- project_type
- language
- limit
- offset

GET /search/content-assets

Filters:

- query
- project_id
- status
- content_type
- source
- limit
- offset

Response shape:

    {
      "total": 0,
      "limit": 20,
      "offset": 0,
      "items": []
    }
    ''',
)


append_once(
    "docs/frontend-routes.md",
    "## Release Pack N Routes",
    r'''
## Release Pack N Routes

Added routes:

    /search
    /search/projects
    /search/content-assets
    /content-assets/[assetId]

Purpose:

Expose search, filters, and content asset detail pages.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack N Completed",
    r'''
## Release Pack N Completed

Name:

Search + Filters + Content Asset Detail + Export UX

Added backend files:

- backend/src/services/search_service.py
- backend/src/api/search.py
- backend/tests/smoke_test_search.py

Added frontend files:

- frontend/src/components/search-filter-card.tsx
- frontend/src/components/asset-body-preview.tsx
- frontend/src/app/search/page.tsx
- frontend/src/app/search/projects/page.tsx
- frontend/src/app/search/content-assets/page.tsx
- frontend/src/app/content-assets/[assetId]/page.tsx

Updated files:

- backend/src/main.py
- backend/src/api/__init__.py
- scripts/backend-check.ps1
- frontend/src/lib/api-client.ts
- frontend/src/lib/types.ts
- frontend/src/components/app-nav.tsx
- frontend/src/app/projects/page.tsx
- frontend/src/app/content-assets/page.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- docs/backend-api.md
- docs/frontend-routes.md
- docs/project-status.md

Added behavior:

- read-only backend search API
- project search filters
- content asset search filters
- frontend search pages
- content asset detail page
- asset markdown export endpoint link
- stronger frontend check
- backend smoke test for search

Next recommended Release Pack:

Release Pack O: Operational Actions and Safe POST UI

Suggested scope:

- safe export trigger UI
- safe backup trigger UI
- project status update UI
- content asset status update UI
- confirmation-first UI actions
- no delete operations
    ''',
)

print("Release Pack N applied successfully.")
