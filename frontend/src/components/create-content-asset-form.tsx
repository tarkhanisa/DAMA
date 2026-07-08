"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import type { ContentAsset, Project } from "../lib/types";
import { FormStatus } from "./form-status";

type CreateContentAssetFormProps = {
  projects: Project[];
};

export function CreateContentAssetForm({ projects }: CreateContentAssetFormProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [contentType, setContentType] = useState("blog_post");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [statusValue, setStatusValue] = useState("draft");
  const [createdAsset, setCreatedAsset] = useState<ContentAsset | null>(null);
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
      const asset = await damaApi.createContentAsset({
        project_id: projectId,
        content_type: contentType,
        title,
        body,
        status: statusValue,
        source: "manual",
        metadata: {
          created_from: "frontend_shell"
        }
      });

      setCreatedAsset(asset);
      setStatus({
        type: "success",
        message: "Content asset created successfully."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Content asset creation failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <label>
        Project
        <select
          required
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        Content type
        <input
          required
          value={contentType}
          onChange={(event) => setContentType(event.target.value)}
          placeholder="blog_post"
        />
      </label>

      <label>
        Title
        <input
          required
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Content title"
        />
      </label>

      <label>
        Status
        <select
          value={statusValue}
          onChange={(event) => setStatusValue(event.target.value)}
        >
          <option value="draft">draft</option>
          <option value="review">review</option>
          <option value="approved">approved</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
      </label>

      <label>
        Body
        <textarea
          required
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Write content body..."
        />
      </label>

      <button type="submit" disabled={isSubmitting || projects.length === 0}>
        {isSubmitting ? "Creating..." : "Create content asset"}
      </button>

      <FormStatus
        type={projects.length === 0 ? "error" : status.type}
        message={
          projects.length === 0
            ? "Create a project first."
            : status.message
        }
      />

      {createdAsset ? (
        <a className="form-result-link" href={`/projects/${createdAsset.project_id}`}>
          Open asset project
        </a>
      ) : null}
    </form>
  );
}
