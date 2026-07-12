"use client";

import { useState } from "react";

type RunPublishingQueueItemActionProps = {
  apiBaseUrl: string;
  queueId: string;
  status: string;
};

export function RunPublishingQueueItemAction({
  apiBaseUrl,
  queueId,
  status
}: RunPublishingQueueItemActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  const canRun = !["running", "sent", "cancelled"].includes(status);

  async function handleRun() {
    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/queue/${queueId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({})
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در اجرای صف: HTTP ${response.status}`);
        return;
      }

      const nextStatus = payload.item?.status ?? "unknown";
      setMessage(`اجرا انجام شد: ${nextStatus}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <button type="button" onClick={handleRun} disabled={isRunning || !canRun}>
        {isRunning ? "در حال اجرا..." : "اجرای صف"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
