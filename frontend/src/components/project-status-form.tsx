"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import { FormStatus } from "./form-status";
import { OperationResult } from "./operation-result";

type ProjectStatusFormProps = {
  projectId: string;
  currentStatus: string;
};

const projectStatuses = ["draft", "active", "review", "paused", "completed", "archived"];

export function ProjectStatusForm({ projectId, currentStatus }: ProjectStatusFormProps) {
  const [statusValue, setStatusValue] = useState(currentStatus);
  const [result, setResult] = useState<unknown>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });
    setResult(null);

    try {
      const response = await damaApi.updateProjectStatus(projectId, statusValue);
      setResult(response);
      setStatus({
        type: "success",
        message: "Project status updated."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Project status update failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card compact-form" onSubmit={handleSubmit}>
      <label>
        Project status
        <select
          value={statusValue}
          onChange={(event) => setStatusValue(event.target.value)}
        >
          {projectStatuses.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Updating..." : "Update project status"}
      </button>

      <FormStatus type={status.type} message={status.message} />
      <OperationResult title="Status update result" result={result} />
    </form>
  );
}
