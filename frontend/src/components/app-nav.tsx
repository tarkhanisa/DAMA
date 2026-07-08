const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/content-assets", label: "Content Assets" },
  { href: "/workflows", label: "Workflows" },
  { href: "/search", label: "Search" },
  { href: "/operations", label: "Operations" },
  { href: "/exports", label: "Exports" },
  { href: "/maintenance", label: "Maintenance" }
];

export function AppNav() {
  return (
    <nav className="app-nav">
      <a className="brand-link" href="/">
        DAMA
      </a>

      <div>
        {navItems.map((item) => (
          <a key={item.href} href={item.href}>
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
