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
