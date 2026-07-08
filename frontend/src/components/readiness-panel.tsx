type ReadinessPanelProps = {
  readiness: {
    has_projects: boolean;
    has_content_assets: boolean;
    has_exports: boolean;
    dashboard_ready: boolean;
    workflow_ready: boolean;
    export_ready: boolean;
  };
};

const readinessLabels: Record<string, string> = {
  has_projects: "Projects exist",
  has_content_assets: "Content assets exist",
  has_exports: "Exports exist",
  dashboard_ready: "Dashboard ready",
  workflow_ready: "Workflow ready",
  export_ready: "Export ready"
};

export function ReadinessPanel({ readiness }: ReadinessPanelProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">Readiness</p>
        <h2>System readiness</h2>
      </div>

      <div className="readiness-grid">
        {Object.entries(readiness).map(([key, value]) => (
          <div key={key} className={value ? "readiness-item is-ready" : "readiness-item"}>
            <span>{value ? "Ready" : "Pending"}</span>
            <strong>{readinessLabels[key] ?? key}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
