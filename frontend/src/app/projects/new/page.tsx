import { CreateProjectForm } from "../../../components/create-project-form";
import { PageHeader } from "../../../components/page-header";

export default function NewProjectPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Projects"
        title="Create project"
        lead="Create a safe new DAMA project record for content workflows."
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">New Project</p>
          <h2>Project details</h2>
        </div>

        <CreateProjectForm />
      </section>
    </main>
  );
}
