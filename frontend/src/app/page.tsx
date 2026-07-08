import { DAMA_API_BASE_URL } from "../lib/api-client";

const sections = [
  "Dashboard",
  "Projects",
  "Content Assets",
  "Workflows",
  "Exports",
  "Maintenance",
  "Developer"
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">DAMA Frontend Foundation</p>
        <h1>AI Content Automation Platform</h1>
        <p className="lead">
          This is the first frontend foundation for DAMA. The backend is already
          API-first and dashboard-ready.
        </p>

        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/docs`}>Open API Docs</a>
          <a href={`${DAMA_API_BASE_URL}/dashboard/summary`}>
            Dashboard Summary
          </a>
          <a href={`${DAMA_API_BASE_URL}/developer/frontend-contract`}>
            Frontend Contract
          </a>
        </div>
      </section>

      <section className="grid">
        {sections.map((section) => (
          <article key={section} className="card">
            <h2>{section}</h2>
            <p>Ready for the next frontend implementation step.</p>
          </article>
        ))}
      </section>
    </main>
  );
}
