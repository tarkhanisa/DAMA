import { ActionCard } from "../../components/action-card";
import { CountBreakdown } from "../../components/count-breakdown";
import { DataTable } from "../../components/data-table";
import { JsonPreview } from "../../components/json-preview";
import { StatCard } from "../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../lib/api-client";
import type { MaintenanceStatus } from "../../lib/types";

async function loadMaintenanceStatus(): Promise<MaintenanceStatus | null> {
  try {
    return await damaApi.maintenanceStatus();
  } catch {
    return null;
  }
}

export default async function MaintenancePage() {
  const status = await loadMaintenanceStatus();

  if (!status) {
    return (
      <main className="page-shell">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Maintenance</p>
            <h1>Maintenance status unavailable</h1>
          </div>
          <p className="empty-state">
            Start the backend first, then refresh this page.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="page-heading">
        <p className="eyebrow">Maintenance</p>
        <h1>Local maintenance center</h1>
        <p className="lead">
          Inspect database state, export files, backup files, and safe maintenance endpoints.
        </p>

        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/maintenance/status`}>
            Raw Maintenance Status
          </a>
          <a href={`${DAMA_API_BASE_URL}/maintenance/database/backup`}>
            Backup Endpoint
          </a>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          label="Database"
          value={status.database.exists ? "Ready" : "Missing"}
          helper={`${status.database.size_bytes} bytes`}
        />
        <StatCard
          label="Exports"
          value={status.exports.file_count}
          helper={`${status.exports.total_size_bytes} bytes`}
        />
        <StatCard
          label="Backups"
          value={status.backups.file_count}
          helper={`${status.backups.total_size_bytes} bytes`}
        />
        <StatCard
          label="Maintenance"
          value={status.maintenance_ready ? "Ready" : "Pending"}
          helper="Local maintenance API"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Create Database Backup"
          description="Use the POST endpoint or DAMA autopilot backup command to create a local SQLite backup."
          href={`${DAMA_API_BASE_URL}/maintenance/database/backup`}
          label="POST endpoint"
        />
        <ActionCard
          title="Autopilot Backup"
          description="Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dama.ps1 backup"
          label="Local command"
        />
        <ActionCard
          title="Backend Check"
          description="Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\dama.ps1 check"
          label="Local command"
        />
      </section>

      <section className="breakdown-grid two-card-grid">
        <CountBreakdown title="Database tables" items={status.database.tables} />
        <CountBreakdown
          title="Directory files"
          items={{
            exports: status.exports.file_count,
            backups: status.backups.file_count
          }}
        />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Backups</p>
            <h2>Recent backup files</h2>
          </div>

          <DataTable
            emptyLabel="No backup files found."
            items={status.backups.recent}
            columns={[
              {
                key: "file",
                label: "File",
                render: (item) => item.file_name
              },
              {
                key: "size",
                label: "Size",
                render: (item) => `${item.size_bytes} bytes`
              }
            ]}
          />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Exports</p>
            <h2>Recent export files</h2>
          </div>

          <DataTable
            emptyLabel="No export files found."
            items={status.exports.recent}
            columns={[
              {
                key: "file",
                label: "File",
                render: (item) => item.file_name
              },
              {
                key: "size",
                label: "Size",
                render: (item) => `${item.size_bytes} bytes`
              }
            ]}
          />
        </section>
      </section>

      <JsonPreview title="Maintenance payload" data={status} />
    </main>
  );
}
