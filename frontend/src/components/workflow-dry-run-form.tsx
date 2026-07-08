"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import type { BatchGenerateResponse } from "../lib/types";
import { FormStatus } from "./form-status";

type WorkflowDryRunFormProps = {
  projectId: string;
};

export function WorkflowDryRunForm({ projectId }: WorkflowDryRunFormProps) {
  const [model, setModel] = useState("qwen2.5-coder:7b");
  const [topic, setTopic] = useState("");
  const [contentTypes, setContentTypes] = useState("");
  const [maxOutputs, setMaxOutputs] = useState("2");
  const [result, setResult] = useState<BatchGenerateResponse | null>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus({ type: "idle" });

    try {
      const response = await damaApi.batchGenerateDryRun(projectId, {
        model,
        topic: topic || undefined,
        content_types: contentTypes
          ? contentTypes.split(",").map((item) => item.trim()).filter(Boolean)
          : undefined,
        max_outputs: Number(maxOutputs) || 1,
        dry_run: true
      });

      setResult(response);
      setStatus({
        type: "success",
        message: "Dry run completed successfully."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Dry run failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="form-grid">
      <form className="form-card" onSubmit={handleSubmit}>
        <label>
          Model
          <input
            required
            value={model}
            onChange={(event) => setModel(event.target.value)}
          />
        </label>

        <label>
          Topic
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Optional topic override"
          />
        </label>

        <label>
          Content types
          <input
            value={contentTypes}
            onChange={(event) => setContentTypes(event.target.value)}
            placeholder="Optional: blog_post, social_caption"
          />
        </label>

        <label>
          Max outputs
          <input
            min="1"
            max="10"
            type="number"
            value={maxOutputs}
            onChange={(event) => setMaxOutputs(event.target.value)}
          />
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Running..." : "Run dry run"}
        </button>

        <FormStatus type={status.type} message={status.message} />
      </form>

      <section className="panel form-result-panel">
        <div className="panel-heading">
          <p className="eyebrow">Dry Run Result</p>
          <h2>Planned outputs</h2>
        </div>

        {result ? (
          <pre className="code-block">{JSON.stringify(result, null, 2)}</pre>
        ) : (
          <p className="empty-state">
            Run a dry run to preview planned outputs before generation.
          </p>
        )}
      </section>
    </div>
  );
}
