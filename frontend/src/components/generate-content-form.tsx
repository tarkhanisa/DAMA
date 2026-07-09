"use client";

import { FormEvent, useMemo, useState } from "react";

type ProjectOption = {
  id: string;
  name: string;
  status?: string;
  project_type?: string;
};

type ContentTypeOption = {
  key: string;
  label: string;
  description?: string;
};

type ModelOption = {
  name: string;
  provider?: string;
};

type GenerateContentFormProps = {
  apiBaseUrl: string;
  projects: ProjectOption[];
  contentTypes: ContentTypeOption[];
  models: ModelOption[];
};

type GenerationResult = {
  ok: boolean;
  endpoint: string;
  raw: unknown;
  outputText: string;
  assetId?: string;
  message?: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getNestedString(source: unknown, keys: string[]): string {
  let current: unknown = source;

  for (const key of keys) {
    const record = asRecord(current);
    current = record[key];
  }

  return typeof current === "string" ? current : "";
}

function extractOutput(payload: unknown): string {
  const directKeys = [
    "content",
    "text",
    "output",
    "result",
    "body",
    "generated_content",
    "generated_text",
    "message"
  ];

  const record = asRecord(payload);

  for (const key of directKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  const nestedCandidates = [
    ["asset", "body"],
    ["content_asset", "body"],
    ["data", "body"],
    ["data", "content"],
    ["data", "text"],
    ["generation", "content"],
    ["generation", "text"]
  ];

  for (const candidate of nestedCandidates) {
    const value = getNestedString(payload, candidate);
    if (value.trim()) {
      return value;
    }
  }

  return JSON.stringify(payload, null, 2);
}

function extractAssetId(payload: unknown): string | undefined {
  const record = asRecord(payload);

  const directKeys = ["asset_id", "content_asset_id", "id"];

  for (const key of directKeys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  const nestedCandidates = [
    ["asset", "id"],
    ["content_asset", "id"],
    ["data", "asset_id"],
    ["data", "content_asset_id"],
    ["data", "id"]
  ];

  for (const candidate of nestedCandidates) {
    const value = getNestedString(payload, candidate);
    if (value.trim()) {
      return value;
    }
  }

  return undefined;
}

async function postJson(
  endpoint: string,
  payload: Record<string, unknown>
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  let data: unknown;

  try {
    data = await response.json();
  } catch {
    data = await response.text();
  }

  return {
    ok: response.ok,
    status: response.status,
    data
  };
}

export function GenerateContentForm({
  apiBaseUrl,
  projects,
  contentTypes,
  models
}: GenerateContentFormProps) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [contentType, setContentType] = useState(contentTypes[0]?.key ?? "");
  const [model, setModel] = useState(models[0]?.name ?? "");
  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [saveOutput, setSaveOutput] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState("");

  const canSubmit = useMemo(() => {
    return Boolean(projectId && contentType && brief.trim() && !isGenerating);
  }, [brief, contentType, isGenerating, projectId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      setError("Choose a project, content type, and write a brief first.");
      return;
    }

    setIsGenerating(true);
    setError("");
    setResult(null);

    const basePayload = {
      project_id: projectId,
      content_type: contentType,
      title: title.trim() || undefined,
      brief: brief.trim(),
      prompt: brief.trim(),
      model: model || undefined,
      provider: "ollama",
      save_output: saveOutput
    };

    try {
      const contentEndpoint = `${apiBaseUrl}/content/generate`;
      const contentResponse = await postJson(contentEndpoint, basePayload);

      if (contentResponse.ok) {
        setResult({
          ok: true,
          endpoint: contentEndpoint,
          raw: contentResponse.data,
          outputText: extractOutput(contentResponse.data),
          assetId: extractAssetId(contentResponse.data)
        });
        return;
      }

      const workflowEndpoint = `${apiBaseUrl}/workflows/projects/${projectId}/generate`;
      const workflowResponse = await postJson(workflowEndpoint, {
        content_type: contentType,
        title: title.trim() || undefined,
        brief: brief.trim(),
        prompt: brief.trim(),
        model: model || undefined,
        provider: "ollama",
        save_output: saveOutput
      });

      if (workflowResponse.ok) {
        setResult({
          ok: true,
          endpoint: workflowEndpoint,
          raw: workflowResponse.data,
          outputText: extractOutput(workflowResponse.data),
          assetId: extractAssetId(workflowResponse.data)
        });
        return;
      }

      setResult({
        ok: false,
        endpoint: workflowEndpoint,
        raw: workflowResponse.data,
        outputText: extractOutput(workflowResponse.data),
        message: `Primary endpoint failed with HTTP ${contentResponse.status}; fallback failed with HTTP ${workflowResponse.status}.`
      });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="generation-grid">
      <form className="panel generation-form" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <p className="eyebrow">Single Generation</p>
          <h2>Generate content</h2>
        </div>

        <label>
          Project
          <select
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
          >
            {projects.length > 0 ? (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            ) : (
              <option value="">No projects found</option>
            )}
          </select>
        </label>

        <label>
          Content type
          <select
            value={contentType}
            onChange={(event) => setContentType(event.target.value)}
          >
            {contentTypes.length > 0 ? (
              contentTypes.map((type) => (
                <option key={type.key} value={type.key}>
                  {type.label}
                </option>
              ))
            ) : (
              <option value="">No content types found</option>
            )}
          </select>
        </label>

        <label>
          Model
          <select value={model} onChange={(event) => setModel(event.target.value)}>
            {models.length > 0 ? (
              models.map((modelOption) => (
                <option key={modelOption.name} value={modelOption.name}>
                  {modelOption.name}
                </option>
              ))
            ) : (
              <option value="">Backend default model</option>
            )}
          </select>
        </label>

        <label>
          Optional title
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Example: Gorgoran pitch summary"
          />
        </label>

        <label>
          Brief
          <textarea
            value={brief}
            onChange={(event) => setBrief(event.target.value)}
            rows={8}
            placeholder="Write the content request here..."
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={saveOutput}
            onChange={(event) => setSaveOutput(event.target.checked)}
          />
          <span>save_output  store generated result as a content asset when backend supports it</span>
        </label>

        {error ? <p className="form-error">{error}</p> : null}

        <button type="submit" disabled={!canSubmit}>
          {isGenerating ? "Generating..." : "Generate"}
        </button>
      </form>

      <section className="panel generation-output">
        <div className="panel-heading">
          <p className="eyebrow">Result</p>
          <h2>Generated output</h2>
        </div>

        {result ? (
          <>
            <div className="health-list">
              <div>
                <strong>Status</strong>
                <span>{result.ok ? "Generated" : "Generation failed"}</span>
              </div>
              <div>
                <strong>Endpoint</strong>
                <span>{result.endpoint}</span>
              </div>
              {result.message ? (
                <div>
                  <strong>Message</strong>
                  <span>{result.message}</span>
                </div>
              ) : null}
              {result.assetId ? (
                <div>
                  <strong>Saved asset</strong>
                  <a href={`/content-assets/${result.assetId}`}>
                    Open content asset
                  </a>
                </div>
              ) : null}
            </div>

            <pre className="generated-output">{result.outputText}</pre>

            <details>
              <summary>Raw response</summary>
              <pre className="json-block">{JSON.stringify(result.raw, null, 2)}</pre>
            </details>
          </>
        ) : (
          <p className="muted-note">
            Fill the form and run a single safe generation. Batch execution is intentionally not exposed here.
          </p>
        )}
      </section>
    </div>
  );
}
