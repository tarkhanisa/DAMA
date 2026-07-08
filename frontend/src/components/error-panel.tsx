type ErrorPanelProps = {
  eyebrow?: string;
  title: string;
  message: string;
  command?: string;
};

export function ErrorPanel({
  eyebrow = "Error",
  title,
  message,
  command
}: ErrorPanelProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      <p className="empty-state">{message}</p>
      {command ? <pre className="code-block">{command}</pre> : null}
    </section>
  );
}
