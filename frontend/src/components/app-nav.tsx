"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/projects", label: "پروژه‌ها" },
  { href: "/content-assets", label: "محتواها" },
  { href: "/generate", label: "تولید محتوا" },
  { href: "/publishing", label: "انتشار" },
  { href: "/publishing/variants", label: "نسخه‌سازی" },
  { href: "/publishing/attempts", label: "گزارش انتشار" },
  { href: "/workflows", label: "جریان کار" },
  { href: "/search", label: "جستجو" },
  { href: "/runtime", label: "سلامت سیستم" },
  { href: "/operations", label: "عملیات" },
  { href: "/exports", label: "خروجی‌ها" },
  { href: "/maintenance", label: "نگهداری" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="ناوبری دامامدیا">
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
