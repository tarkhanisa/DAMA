"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/content-assets", label: "Content" },
  { href: "/generate", label: "Generate" },
  { href: "/workflows", label: "Workflows" },
  { href: "/search", label: "Search" },
  { href: "/runtime", label: "Runtime" },
  { href: "/operations", label: "Operations" },
  { href: "/exports", label: "Exports" },
  { href: "/maintenance", label: "Maintenance" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="DAMA navigation">
      {navItems.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "active" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
