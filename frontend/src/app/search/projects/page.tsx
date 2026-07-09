import { DataTable, StatusPill } from "../../../components/data-table";
import { PageHeader } from "../../../components/page-header";
import { SearchFilterCard } from "../../../components/search-filter-card";
import { StatCard } from "../../../components/stat-card";
import { damaApi } from "../../../lib/api-client";
import type { Project, SearchResponse } from "../../../lib/types";

type SearchParams = Record<string, string | string[] | undefined>;

type SearchProjectsPageProps = {
  searchParams?: Promise<SearchParams>;
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
              render: (project) => project.language ?? ""
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
