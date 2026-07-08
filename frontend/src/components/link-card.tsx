type LinkCardProps = {
  title: string;
  description: string;
  href: string;
};

export function LinkCard({ title, description, href }: LinkCardProps) {
  return (
    <a className="link-card" href={href}>
      <span>{title}</span>
      <p>{description}</p>
    </a>
  );
}
