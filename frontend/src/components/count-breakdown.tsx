type CountBreakdownProps = {
  title: string;
  items: Record<string, number>;
};

export function CountBreakdown({ title, items }: CountBreakdownProps) {
  const entries = Object.entries(items);

  return (
    <article className="breakdown-card">
      <h3>{title}</h3>

      {entries.length === 0 ? (
        <p>No data yet.</p>
      ) : (
        <ul>
          {entries.map(([key, value]) => (
            <li key={key}>
              <span>{key}</span>
              <strong>{value}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
