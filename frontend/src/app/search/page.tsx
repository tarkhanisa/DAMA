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
