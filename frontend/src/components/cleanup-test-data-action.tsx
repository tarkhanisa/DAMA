"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type CleanupTestDataActionProps = {
  apiBaseUrl: string;
};

export function CleanupTestDataAction({ apiBaseUrl }: CleanupTestDataActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function handleCleanup() {
    const confirmed = window.confirm(
      "داده‌های تستی صف، نسخه‌ها و گزارش‌ها پاک می‌شوند. قبل از حذف backup گرفته می‌شود. ادامه می‌دهی؟"
    );

    if (!confirmed) {
      return;
    }

    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/cleanup/test-data/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          backup: true
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(`HTTP ${response.status}`));
        return;
      }

      const removed = payload.totals?.removed ?? 0;
      const backupPath = payload.backup_path ? ` backup: ${payload.backup_path}` : "";

      setMessage(`پاک‌سازی انجام شد. تعداد حذف‌شده: ${removed}.${backupPath}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <button type="button" onClick={handleCleanup} disabled={isRunning}>
        {isRunning ? "در حال پاک‌سازی..." : "پاک‌سازی داده‌های تستی"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
