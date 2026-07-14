"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type RunLocalVideoJobActionProps = {
  apiBaseUrl: string;
  jobId: string;
};

export function RunLocalVideoJobAction({ apiBaseUrl, jobId }: RunLocalVideoJobActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function run(mode: "dry_run" | "local") {
    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/local-video/jobs/${jobId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ mode })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage(payload.message ?? "اجرا انجام شد.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action local-video-actions">
      <button type="button" onClick={() => run("dry_run")} disabled={isRunning}>
        {isRunning ? "در حال اجرا..." : "Dry-run امن"}
      </button>

      <button type="button" onClick={() => run("local")} disabled={isRunning}>
        اجرای موتور لوکال
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
