"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/produce", label: "تولید" },
  { href: "/publishing", label: "انتشار" },
  { href: "/other", label: "سایر" }
];

function showClosedScreen() {
  document.documentElement.innerHTML = `
    <html lang="fa" dir="rtl">
      <head>
        <title>DAMA بسته شد</title>
        <style>
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0f172a;
            color: #fff;
          }
          main {
            width: min(560px, calc(100vw - 32px));
            padding: 32px;
            border: 1px solid rgba(255,255,255,.16);
            border-radius: 24px;
            background: rgba(255,255,255,.08);
            text-align: center;
          }
          h1 { margin: 0 0 12px; font-size: 28px; }
          p { margin: 0; line-height: 2; color: rgba(255,255,255,.76); }
        </style>
      </head>
      <body>
        <main>
          <h1>خروج امن انجام شد</h1>
          <p>سرورهای محلی DAMA در حال بسته‌شدن هستند. اگر این تب خودکار بسته نشد، می‌توانی آن را دستی ببندی.</p>
        </main>
      </body>
    </html>
  `;
}

export function AppNav() {
  const pathname = usePathname();
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (pathname && pathname !== "/other/exit") {
      window.localStorage.setItem("dama:last-route", pathname);

      fetch(`${API_BASE_URL}/publishing/operator/session/route`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          last_route: pathname
        })
      }).catch(() => {
        // Local backend may be offline while frontend renders.
      });
    }
  }, [pathname]);

  async function handleSafeExit() {
    const confirmed = window.confirm(
      "خروج امن انجام شود؟ آخرین صفحه ذخیره می‌شود، backup گرفته می‌شود و سرورهای DAMA بسته می‌شوند."
    );

    if (!confirmed) {
      return;
    }

    const lastRoute =
      window.localStorage.getItem("dama:last-route") ||
      pathname ||
      "/";

    setIsExiting(true);

    try {
      await fetch(`${API_BASE_URL}/publishing/operator/session/safe-exit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          last_route: lastRoute,
          backup: true,
          shutdown: true
        })
      });
    } catch {
      // Even if the response is interrupted by shutdown, continue closing the UI.
    }

    window.setTimeout(() => {
      try {
        window.open("", "_self");
        window.close();
      } catch {
        // Browser may block closing tabs it did not open by script.
      }

      window.setTimeout(() => {
        showClosedScreen();
      }, 500);
    }, 900);
  }

  return (
    <div className="app-nav-shell">
      <nav className="app-nav" aria-label="ناوبری اصلی DAMA">
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

      <button
        className="safe-exit-top-button"
        type="button"
        onClick={handleSafeExit}
        disabled={isExiting}
      >
        {isExiting ? "در حال خروج..." : "خروج امن"}
      </button>
    </div>
  );
}
