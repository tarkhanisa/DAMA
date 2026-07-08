type RecentItem = {
  id?: string;
  name?: string;
  title?: string;
  project_type?: string;
  content_type?: string;
  status?: string;
  source?: string;
  created_at?: string;
};

type RecentListProps = {
  title: string;
  eyebrow: string;
  emptyLabel: string;
  items: RecentItem[];
};

export function RecentList({ title, eyebrow, emptyLabel, items }: RecentListProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>

      {items.length === 0 ? (
        <p className="empty-state">{emptyLabel}</p>
      ) : (
        <div className="recent-list">
          {items.map((item, index) => (
            <article key={item.id ?? index} className="recent-item">
              <div>
                <h3>{item.name ?? item.title ?? "Untitled"}</h3>
                <p>
                  {item.project_type ?? item.content_type ?? "item"}
                  {item.source ? ` · ${item.source}` : ""}
                </p>
              </div>
              <span>{item.status ?? "unknown"}</span>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
