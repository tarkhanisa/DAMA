import { DataTable, StatusPill } from "../../../components/data-table";
import { PageHeader } from "../../../components/page-header";
import { SearchFilterCard } from "../../../components/search-filter-card";
import { StatCard } from "../../../components/stat-card";
import { damaApi } from "../../../lib/api-client";
import type { ContentAsset, SearchResponse } from "../../../lib/types";

type SearchParams = Record<string, string | string[] | undefined>;

type SearchContentAssetsPageProps = {
  searchParams?: Promise<SearchParams>;
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
