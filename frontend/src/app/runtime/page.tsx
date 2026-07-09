import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

type RuntimeStorageItem = {
  label: string;
  path: string;
  exists: boolean;
  is_directory: boolean;
  writable: boolean;
  status: string;
};

type RuntimeHealth = {
  ok: boolean;
  status: string;
  checked_at: string;
  backend: {
    status: string;
    project_root: string;
    backend_root: string;
    runtime: string;
  };
  storage: RuntimeStorageItem[];
  ollama: {
    status: string;
    base_url: string;
    reachable: boolean;
    model_count: number;
    models: string[];
    message?: string;
  };
  config: {
    environment: Record<string, string>;
    has_next_public_api_url: boolean;
    secrets_redacted: boolean;
  };
  operator_notes: string[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

function fallbackHealth(message: string): RuntimeHealth {
  return {
    ok: false,
    status: "warning",
    checked_at: new Date().toISOString(),
    backend: {
      status: "warning",
      project_root: "unknown",
      backend_root: "unknown",
      runtime: "fastapi"
    },
    storage: [],
    ollama: {
      status: "unknown",
      base_url: "unknown",
      reachable: false,
      model_count: 0,
      models: [],
      message
    },
    config: {
      environment: {},
      has_next_public_api_url: Boolean(process.env.NEXT_PUBLIC_DAMA_API_BASE_URL),
      secrets_redacted: true
    },
    operator_notes: [
      "Frontend could not reach the backend runtime health endpoint.",
      "Start the backend first, then refresh this page."
    ]
  };
}

async function loadRuntimeHealth(): Promise<RuntimeHealth> {
  try {
    const response = await fetch(`${API_BASE_URL}/runtime/health`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return fallbackHealth(`Backend responded with HTTP ${response.status}.`);
    }

    return (await response.json()) as RuntimeHealth;
  } catch (error) {
    return fallbackHealth(error instanceof Error ? error.message : "Unknown error");
  }
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`status-badge status-${status}`}>{status}</span>;
}

export default async function RuntimePage() {
  const health = await loadRuntimeHealth();

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Runtime"
        title="Operator runtime health"
        lead="A safe read-only view of backend availability, Ollama reachability, local storage paths, and public configuration."
      >
        <div className="actions">
          <a href={`${API_BASE_URL}/runtime/health`}>Raw Runtime JSON</a>
          <a href={`${API_BASE_URL}/docs`}>API Docs</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Overall" value={health.status} helper="Runtime status" />
        <StatCard
          label="Backend"
          value={health.backend.status}
          helper={health.backend.runtime}
        />
        <StatCard
          label="Ollama"
          value={health.ollama.reachable ? "reachable" : "not reachable"}
          helper={health.ollama.base_url}
        />
        <StatCard
          label="Models"
          value={health.ollama.model_count}
          helper="Local Ollama model count"
        />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Backend</p>
            <h2>Backend runtime</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>Status</strong>
              <StatusBadge status={health.backend.status} />
            </div>
            <div>
              <strong>Project root</strong>
              <span>{health.backend.project_root}</span>
            </div>
            <div>
              <strong>Backend root</strong>
              <span>{health.backend.backend_root}</span>
            </div>
            <div>
              <strong>Checked at</strong>
              <span>{health.checked_at}</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Ollama</p>
            <h2>Local model service</h2>
          </div>

          <div className="health-list">
            <div>
              <strong>Status</strong>
              <StatusBadge status={health.ollama.status} />
            </div>
            <div>
              <strong>Reachable</strong>
              <span>{health.ollama.reachable ? "Yes" : "No"}</span>
            </div>
            <div>
              <strong>Base URL</strong>
              <span>{health.ollama.base_url}</span>
            </div>
            <div>
              <strong>Models</strong>
              <span>
                {health.ollama.models.length > 0
                  ? health.ollama.models.join(", ")
                  : "No models listed"}
              </span>
            </div>
          </div>

          {health.ollama.message ? (
            <p className="muted-note">{health.ollama.message}</p>
          ) : null}
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Storage</p>
          <h2>Local runtime paths</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>Label</th>
                <th>Status</th>
                <th>Exists</th>
                <th>Writable</th>
                <th>Path</th>
              </tr>
            </thead>
            <tbody>
              {health.storage.length > 0 ? (
                health.storage.map((item) => (
                  <tr key={item.label}>
                    <td>{item.label}</td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>{item.exists ? "Yes" : "No"}</td>
                    <td>{item.writable ? "Yes" : "No"}</td>
                    <td>{item.path}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>No storage data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Config</p>
            <h2>Public configuration</h2>
          </div>

          <pre className="json-block">
            {JSON.stringify(health.config, null, 2)}
          </pre>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Operator Notes</p>
            <h2>Read-only safety notes</h2>
          </div>

          <ul className="note-list">
            {health.operator_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}
