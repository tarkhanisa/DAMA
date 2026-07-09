from pathlib import Path
import shutil

ROOT = Path("I:/DAMA")
target = ROOT / "frontend/src/app/content-assets/[assetId]/page.tsx"

content = r'''
import { AssetBodyPreview } from "../../../components/asset-body-preview";
import { ContentAssetStatusForm } from "../../../components/content-asset-status-form";
import { ErrorPanel } from "../../../components/error-panel";
import { ExportContentAssetAction } from "../../../components/export-content-asset-action";
import { JsonPreview } from "../../../components/json-preview";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../../lib/api-client";
import type { ContentAsset } from "../../../lib/types";

type AssetDetailPageProps = {
  params: Promise<{
    assetId: string;
  }>;
};

async function loadAsset(assetId: string): Promise<ContentAsset | null> {
  try {
    return await damaApi.contentAsset(assetId);
  } catch {
    return null;
  }
}

export default async function AssetDetailPage({ params }: AssetDetailPageProps) {
  const { assetId } = await params;
  const asset = await loadAsset(assetId);

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
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Status" value={asset.status} helper="Asset status" />
        <StatCard label="Source" value={asset.source} helper="Asset source" />
        <StatCard label="Type" value={asset.content_type} helper="Content type" />
        <StatCard label="Project" value="Linked" helper={asset.project_id} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Status</p>
            <h2>Update asset status</h2>
          </div>

          <ContentAssetStatusForm assetId={asset.id} currentStatus={asset.status} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Export</p>
            <h2>Markdown export</h2>
          </div>

          <ExportContentAssetAction assetId={asset.id} />
        </section>
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
'''.strip() + "\n"

target.write_text(content, encoding="utf-8")

written = target.read_text(encoding="utf-8")

if "| Promise" in written:
    raise RuntimeError("Patch failed: union params type still exists.")

if "params: Promise" not in written:
    raise RuntimeError("Patch failed: Promise params type not found.")

if "resolveParams" in written:
    raise RuntimeError("Patch failed: old resolveParams helper still exists.")

next_cache = ROOT / "frontend/.next"
if next_cache.exists():
    shutil.rmtree(next_cache)
    print("Removed frontend/.next cache.")

print("Asset detail page patched and verified.")
print("Current params type:")
for line in written.splitlines():
    if "params:" in line:
        print(line)
