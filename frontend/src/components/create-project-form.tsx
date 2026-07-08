"use client";

import { useState } from "react";

import { damaApi } from "../lib/api-client";
import type { Project } from "../lib/types";
import { FormStatus } from "./form-status";

const defaultContentTypes = [
  "blog_post",
  "social_caption",
  "product_description"
];

export function CreateProjectForm() {
  const [name, setName] = useState("");
  const [projectType, setProjectType] = useState("content_campaign");
  const [language, setLanguage] = useState("en");
  const [description, setDescription] = useState("");
  const [contentTypes, setContentTypes] = useState(defaultContentTypes.join(", "));
  const [createdProject, setCreatedProject] = useState<Project | null>(null);
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
      const project = await damaApi.createProject({
        name,
        project_type: projectType,
        language,
        description,
        content_types: contentTypes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      });

      setCreatedProject(project);
      setStatus({
        type: "success",
        message: "Project created successfully."
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Project creation failed."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-card" onSubmit={handleSubmit}>
      <label>
        Project name
        <input
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="DAMA Launch Campaign"
        />
      </label>

      <label>
        Project type
        <select
          value={projectType}
          onChange={(event) => setProjectType(event.target.value)}
        >
          <option value="content_campaign">content_campaign</option>
          <option value="product_launch">product_launch</option>
          <option value="video_package">video_package</option>
        </select>
      </label>

      <label>
        Language
        <input
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          placeholder="en"
        />
      </label>

      <label>
        Content types
        <input
          value={contentTypes}
          onChange={(event) => setContentTypes(event.target.value)}
          placeholder="blog_post, social_caption"
        />
      </label>

      <label>
        Description
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Short project description"
        />
      </label>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create project"}
      </button>

      <FormStatus type={status.type} message={status.message} />

      {createdProject ? (
        <a className="form-result-link" href={`/projects/${createdProject.id}`}>
          Open created project
        </a>
      ) : null}
    </form>
  );
}
