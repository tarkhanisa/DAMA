import { PageHeader } from "../../../../components/page-header";
import { WorkflowDryRunForm } from "../../../../components/workflow-dry-run-form";
import { damaApi } from "../../../../lib/api-client";
import type { Project } from "../../../../lib/types";

type WorkflowDryRunPageProps = {
  params: {
    projectId: string;
  };
};

async function loadProject(projectId: string): Promise<Project | null> {
  try {
    return await damaApi.project(projectId);
  } catch {
    return null;
  }
}

export default async function WorkflowDryRunPage({ params }: WorkflowDryRunPageProps) {
  const project = await loadProject(params.projectId);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Workflow Dry Run"
        title={project ? project.name : "Workflow dry run"}
        lead="Preview planned batch generation outputs without creating content assets."
      />

      <WorkflowDryRunForm projectId={params.projectId} />
    </main>
  );
}
