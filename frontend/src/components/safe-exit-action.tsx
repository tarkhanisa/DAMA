"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type SafeExitActionProps = {
  apiBaseUrl: string;
};

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
          <p>اگر این تب خودکار بسته نشد، می‌توانی آن را دستی ببندی.</p>
        </main>
      </body>
    </html>
  `;
}

export function SafeExitAction({ apiBaseUrl }: SafeExitActionProps) {
  const [isExiting, setIsExiting] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSafeExit() {
    const lastRoute = window.localStorage.getItem("dama:last-route") || "/";
    setIsExiting(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/operator/session/safe-exit`, {
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

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage(payload.message ?? "خروج امن ثبت شد. تا چند ثانیه دیگر DAMA بسته می‌شود.");

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
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));

      window.setTimeout(() => {
        showClosedScreen();
      }, 1200);
    } finally {
      window.setTimeout(() => setIsExiting(false), 3000);
    }
  }

  return (
    <div className="safe-exit-action">
      <button type="button" onClick={handleSafeExit} disabled={isExiting}>
        {isExiting ? "در حال خروج امن..." : "خروج امن و بستن داشبورد"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
