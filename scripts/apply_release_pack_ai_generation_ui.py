from pathlib import Path
import re

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required_lines = [
        '".\\frontend\\src\\app\\generate\\page.tsx",',
        '".\\frontend\\src\\components\\generate-content-form.tsx",',
    ]

    for line in required_lines:
        if line not in text:
            marker = '".\\frontend\\src\\app\\runtime\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)
            else:
                marker = '".\\frontend\\src\\app\\operations\\page.tsx",'
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Generate page does not include GenerateContentForm." not in text:
        check_block = r'''
$GeneratePage = Read-TextFile ".\frontend\src\app\generate\page.tsx"
$GenerateForm = Read-TextFile ".\frontend\src\components\generate-content-form.tsx"

if ($GeneratePage -notmatch "GenerateContentForm") {
    throw "Generate page does not include GenerateContentForm."
}

if ($GenerateForm -notmatch "save_output") {
    throw "Generate form does not expose save_output."
}

if ($GenerateForm -notmatch "/content/generate") {
    throw "Generate form does not call content generation endpoint."
}

if ($GenerateForm -notmatch "/workflows/projects/") {
    throw "Generate form does not include workflow generation fallback."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            check_block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/content-assets", label: "Content" },
  { href: "/generate", label: "Generate" },
  { href: "/workflows", label: "Workflows" },
  { href: "/search", label: "Search" },
  { href: "/runtime", label: "Runtime" },
  { href: "/operations", label: "Operations" },
  { href: "/exports", label: "Exports" },
  { href: "/maintenance", label: "Maintenance" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="DAMA navigation">
      {navItems.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "active" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
    ''',
)


write_file(
    "frontend/src/components/generate-content-form.tsx",
    r'''
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
    ''',
)


write_file(
    "frontend/src/app/generate/page.tsx",
    r'''
import { GenerateContentForm } from "../../components/generate-content-form";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

async function getJson(endpoint: string): Promise<unknown> {
  const response = await fetch(endpoint, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

function normalizeProjects(payload: unknown): ProjectOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.items ?? record.projects ?? record.data);

  return source
    .map((item) => {
      const value = asRecord(item);
      const id = String(value.id ?? "");
      const name = String(value.name ?? value.title ?? id);

      return {
        id,
        name,
        status: typeof value.status === "string" ? value.status : undefined,
        project_type:
          typeof value.project_type === "string" ? value.project_type : undefined
      };
    })
    .filter((project) => project.id && project.name);
}

function normalizeContentTypes(payload: unknown): ContentTypeOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.items ?? record.content_types ?? record.types ?? record.data);

  return source
    .map((item) => {
      if (typeof item === "string") {
        return {
          key: item,
          label: item
        };
      }

      const value = asRecord(item);
      const key = String(value.key ?? value.id ?? value.name ?? "");
      const label = String(value.label ?? value.name ?? value.title ?? key);

      return {
        key,
        label,
        description:
          typeof value.description === "string" ? value.description : undefined
      };
    })
    .filter((type) => type.key && type.label);
}

function normalizeModels(payload: unknown): ModelOption[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.models ?? record.items ?? record.data);

  return source
    .map((item) => {
      if (typeof item === "string") {
        return {
          name: item,
          provider: "ollama"
        };
      }

      const value = asRecord(item);
      const name = String(value.name ?? value.model ?? value.id ?? "");

      return {
        name,
        provider: typeof value.provider === "string" ? value.provider : "ollama"
      };
    })
    .filter((model) => model.name);
}

async function loadProjects(): Promise<ProjectOption[]> {
  try {
    const payload = await getJson(`${API_BASE_URL}/projects`);
    return normalizeProjects(payload);
  } catch {
    return [];
  }
}

async function loadContentTypes(): Promise<ContentTypeOption[]> {
  try {
    const payload = await getJson(`${API_BASE_URL}/content/types`);
    return normalizeContentTypes(payload);
  } catch {
    return [
      { key: "general", label: "General" },
      { key: "article", label: "Article" },
      { key: "summary", label: "Summary" },
      { key: "pitch", label: "Pitch" }
    ];
  }
}

async function loadModels(): Promise<ModelOption[]> {
  try {
    const payload = await getJson(`${API_BASE_URL}/models`);
    return normalizeModels(payload);
  } catch {
    return [];
  }
}

export default async function GeneratePage() {
  const [projects, contentTypes, models] = await Promise.all([
    loadProjects(),
    loadContentTypes(),
    loadModels()
  ]);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="AI Operator"
        title="Generate content"
        lead="Run one safe AI content generation at a time. Batch execution remains intentionally disabled from this page."
      >
        <div className="actions">
          <a href={`${API_BASE_URL}/docs`}>API Docs</a>
          <a href="/content-assets">Content Assets</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Projects" value={projects.length} helper="Available project options" />
        <StatCard label="Content Types" value={contentTypes.length} helper="Available content types" />
        <StatCard label="Models" value={models.length || "Default"} helper="Ollama model options" />
        <StatCard label="Mode" value="Single" helper="No batch execution" />
      </section>

      <GenerateContentForm
        apiBaseUrl={API_BASE_URL}
        projects={projects}
        contentTypes={contentTypes}
        models={models}
      />
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Generation operator */",
    r'''
/* Generation operator */
.generation-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 1rem;
  align-items: start;
}

.generation-form {
  display: grid;
  gap: 1rem;
}

.generation-form label {
  display: grid;
  gap: 0.4rem;
  font-weight: 700;
}

.generation-form input,
.generation-form select,
.generation-form textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 0.85rem;
  padding: 0.8rem 0.9rem;
  background: rgba(255, 255, 255, 0.78);
  color: var(--text);
  font: inherit;
}

.generation-form textarea {
  resize: vertical;
  min-height: 12rem;
}

.checkbox-row {
  display: flex !important;
  grid-template-columns: auto 1fr;
  align-items: flex-start;
  gap: 0.65rem !important;
  font-weight: 500 !important;
  color: var(--muted);
}

.checkbox-row input {
  width: auto;
  margin-top: 0.25rem;
}

.generation-form button {
  border: 0;
  border-radius: 999px;
  padding: 0.9rem 1.2rem;
  font-weight: 800;
  cursor: pointer;
  background: var(--text);
  color: var(--surface);
}

.generation-form button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.form-error {
  color: #9f3030;
  font-weight: 700;
}

.generation-output {
  min-height: 28rem;
}

.generated-output {
  white-space: pre-wrap;
  word-break: break-word;
  margin-top: 1rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .generation-grid {
    grid-template-columns: 1fr;
  }
}
    ''',
)


write_file(
    "docs/ai-generation-operator.md",
    r'''
# DAMA AI Generation Operator

Release Pack U adds a safe single-generation operator UI.

## Frontend Page

    http://localhost:3000/generate

## Behavior

The page supports:

- choosing a project
- choosing a content type
- choosing a model
- writing a brief
- toggling `save_output`
- generating one result at a time
- opening the saved content asset when the backend returns an asset id

## Safety

This page intentionally does not expose:

- batch generation
- destructive actions
- delete operations
- background queues
- automatic mass publishing

## Backend Calls

The UI first tries:

    POST /content/generate

If that endpoint rejects the payload, it tries the project workflow endpoint:

    POST /workflows/projects/{project_id}/generate

This gives the operator UI compatibility with the current backend generation surface while the backend contract continues to evolve.

## Requirement

For real generation, Ollama should be running locally and the selected model should exist.

Recommended local model:

    qwen2.5-coder:7b
    ''',
)


append_once(
    "README.md",
    "## DAMA AI Generation UI",
    r'''
## DAMA AI Generation UI

Run backend and frontend:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-all.ps1

Open:

    http://localhost:3000/generate

The generation page is single-run and safe. Batch execution is intentionally not exposed.
    ''',
)


append_once(
    "docs/production-readiness.md",
    "## AI Generation Operator UI",
    r'''
## AI Generation Operator UI

Release Pack U adds:

- `/generate` frontend page
- single content generation form
- project selector
- content type selector
- model selector
- brief input
- save_output toggle
- generated output preview
- saved asset link when available

Batch generation remains intentionally disabled from this UI.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack U Completed",
    r'''
## Release Pack U Completed

Name:

AI Generation Operator UI

Added files:

- frontend/src/app/generate/page.tsx
- frontend/src/components/generate-content-form.tsx
- docs/ai-generation-operator.md

Updated files:

- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/frontend-check.ps1
- README.md
- docs/production-readiness.md
- docs/project-status.md

Added behavior:

- safe single generation UI
- project selector
- content type selector
- model selector
- brief input
- save_output toggle
- result preview
- saved asset link when available
- fallback from content generation endpoint to workflow generation endpoint

Next recommended Release Pack:

Release Pack V: Project Workspace Polish

Suggested scope:

- project workspace tabs
- assets inside project detail
- generation shortcut inside project page
- workflow dry-run shortcut
- export shortcut
- clearer operator flow per project
    ''',
)


patch_frontend_check()

print("Release Pack U applied successfully.")
