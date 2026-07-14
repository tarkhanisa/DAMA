"use client";

import { useEffect, useState } from "react";

function routeTitle(route: string): string {
  if (route.startsWith("/publishing")) {
    return "ادامه انتشار";
  }

  if (route.startsWith("/produce/video")) {
    return "ادامه تولید ویدیو";
  }

  if (route.startsWith("/produce")) {
    return "ادامه تولید";
  }

  if (route.startsWith("/other")) {
    return "ادامه سایر";
  }

  return "ادامه از آخرین صفحه";
}

export function LastSessionCard() {
  const [lastRoute, setLastRoute] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("dama:last-route") ?? "";

    if (stored && stored !== "/" && stored !== "/other/exit") {
      setLastRoute(stored);
    }
  }, []);

  if (!lastRoute) {
    return null;
  }

  return (
    <section className="last-session-card">
      <div>
        <p className="eyebrow">ادامه کار قبلی</p>
        <h2>{routeTitle(lastRoute)}</h2>
        <p>آخرین صفحه‌ای که داخل پنل باز کرده بودی ذخیره شده است.</p>
      </div>

      <a href={lastRoute}>رفتن به آخرین صفحه</a>
    </section>
  );
}
