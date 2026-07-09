import type { ReactNode } from "react";

type SearchFilterCardProps = {
  title: string;
  children: ReactNode;
};

export function SearchFilterCard({ title, children }: SearchFilterCardProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">Search</p>
        <h2>{title}</h2>
      </div>

      <form className="filter-form" method="get">
        {children}
        <button type="submit">Apply filters</button>
      </form>
    </section>
  );
}
