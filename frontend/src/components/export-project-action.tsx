"use client";

import { damaApi } from "../lib/api-client";
import { SafeActionButton } from "./safe-action-button";

type ExportProjectActionProps = {
  projectId: string;
};

export function ExportProjectAction({ projectId }: ExportProjectActionProps) {
  return (
    <SafeActionButton
      label="Export project bundle"
      confirmLabel="Confirm export"
      successMessage="Project bundle exported."
      action={() => damaApi.exportProjectBundle(projectId)}
    />
  );
}
