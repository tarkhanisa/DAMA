type StatusPillProps = {
  status?: string;
};

export function StatusPill({ status = "unknown" }: StatusPillProps) {
  return <span className="status-pill">{status}</span>;
}
