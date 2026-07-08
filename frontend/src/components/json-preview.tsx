type JsonPreviewProps = {
  title: string;
  data: unknown;
};

export function JsonPreview({ title, data }: JsonPreviewProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">JSON</p>
        <h2>{title}</h2>
      </div>

      <pre className="code-block">{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}
