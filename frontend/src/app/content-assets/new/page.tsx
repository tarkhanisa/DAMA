import { CreateContentAssetForm } from "../../../components/create-content-asset-form";
import { PageHeader } from "../../../components/page-header";
import { damaApi } from "../../../lib/api-client";
import type { Project } from "../../../lib/types";

async function loadProjects(): Promise<Project[]> {
  try {
    return await damaApi.projects();
  } catch {
    return [];
  }
}

export default async function NewContentAssetPage() {
  const projects = await loadProjects();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Content Assets"
        title="Create content asset"
        lead="Create a manual content asset connected to an existing project."
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">New Asset</p>
          <h2>Content details</h2>
        </div>

        <CreateContentAssetForm projects={projects} />
      </section>
    </main>
  );
}
