type PageHeaderProps = {
  eyebrow: string;
  title: string;
  lead?: string;
  children?: React.ReactNode;
};

export function PageHeader({ eyebrow, title, lead, children }: PageHeaderProps) {
  return (
    <section className="page-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {lead ? <p className="lead">{lead}</p> : null}
      {children}
    </section>
  );
}
