type ActionCardProps = {
  title: string;
  description: string;
  href?: string;
  label?: string;
};

export function ActionCard({ title, description, href, label = "Open" }: ActionCardProps) {
  const content = (
    <>
      <span>{title}</span>
      <p>{description}</p>
      <strong>{label}</strong>
    </>
  );

  if (href) {
    return (
      <a className="action-card" href={href}>
        {content}
      </a>
    );
  }

  return <article className="action-card">{content}</article>;
}
