import { ActionCard } from "../../components/action-card";
import { BackupAction } from "../../components/backup-action";
import { CountBreakdown } from "../../components/count-breakdown";
import { DataTable } from "../../components/data-table";
import { ErrorPanel } from "../../components/error-panel";
import { JsonPreview } from "../../components/json-preview";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";
import { DAMA_API_BASE_URL, damaApi } from "../../lib/api-client";
import { formatBytes, formatNumber } from "../../lib/formatters";
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
        <ErrorPanel
          eyebrow="Maintenance"
          title="Maintenance status unavailable"
          message="Start the backend first, then refresh this page."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="Maintenance"
        title="Local maintenance center"
        lead="Inspect database state, export files, backup files, and safe maintenance endpoints."
      >
        <div className="actions">
          <a href={`${DAMA_API_BASE_URL}/maintenance/status`}>
            Raw Maintenance Status
          </a>
          <a href="/operations">
            Operations
          </a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard
          label="Database"
          value={status.database.exists ? "Ready" : "Missing"}
          helper={formatBytes(status.database.size_bytes)}
        />
        <StatCard
          label="Exports"
          value={formatNumber(status.exports.file_count)}
          helper={formatBytes(status.exports.total_size_bytes)}
        />
        <StatCard
          label="Backups"
          value={formatNumber(status.backups.file_count)}
          helper={formatBytes(status.backups.total_size_bytes)}
        />
        <StatCard
          label="Maintenance"
          value={status.maintenance_ready ? "Ready" : "Pending"}
          helper="Local maintenance API"
        />
      </section>

      <section className="action-grid">
        <ActionCard
          title="Operations Center"
          description="Open the confirmation-first operations page."
          href="/operations"
          label="Open"
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

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Backup</p>
          <h2>Create database backup</h2>
        </div>

        <BackupAction />
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
                render: (item) => formatBytes(item.size_bytes)
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
                render: (item) => formatBytes(item.size_bytes)
              }
            ]}
          />
        </section>
      </section>

      <JsonPreview title="Maintenance payload" data={status} />
    </main>
  );
}
