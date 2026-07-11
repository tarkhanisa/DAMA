"use client";

import { useState } from "react";

type TelegramConnectionTestActionProps = {
  apiBaseUrl: string;
};

export function TelegramConnectionTestAction({
  apiBaseUrl
}: TelegramConnectionTestActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  async function handleTest() {
    setIsTesting(true);
    setMessage("");
    setRaw(null);

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/telegram/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ mode })
      });

      const payload = await response.json();
      setRaw(payload);
      setMessage(payload.message ?? `HTTP ${response.status}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">تست اتصال</p>
        <h2>اتصال تلگرام را بررسی کن</h2>
      </div>

      <div className="enhance-variant-action">
        <label>
          حالت تست
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="telegram">تست واقعی Bot</option>
          </select>
        </label>

        <button type="button" onClick={handleTest} disabled={isTesting}>
          {isTesting ? "در حال تست..." : "تست تلگرام"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}
      </div>

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}
