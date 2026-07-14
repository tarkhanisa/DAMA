"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type LocalVideoOutputActionsProps = {
  apiBaseUrl: string;
  jobId: string;
  outputPath: string;
  hasOutput: boolean;
};

export function LocalVideoOutputActions({
  apiBaseUrl,
  jobId,
  outputPath,
  hasOutput
}: LocalVideoOutputActionsProps) {
  const [message, setMessage] = useState("");

  const outputUrl = `${apiBaseUrl}/publishing/local-video/jobs/${jobId}/output`;

  async function copyOutputPath() {
    setMessage("");

    if (!outputPath) {
      setMessage("هنوز مسیر خروجی وجود ندارد.");
      return;
    }

    try {
      await navigator.clipboard.writeText(outputPath);
      setMessage("مسیر خروجی کپی شد.");
    } catch {
      setMessage("کپی خودکار انجام نشد. مسیر را دستی کپی کن.");
    }
  }

  async function openOutputFolder() {
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/local-video/jobs/${jobId}/open-output-folder`,
        {
          method: "POST"
        }
      );

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("درخواست باز کردن فولدر خروجی ارسال شد.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    }
  }

  function openVideoInNewWindow() {
    if (!hasOutput) {
      setMessage("هنوز ویدیوی خروجی ساخته نشده است.");
      return;
    }

    window.open(outputUrl, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="local-video-actions">
      <button type="button" onClick={openVideoInNewWindow} disabled={!hasOutput}>
        مشاهده ویدیو
      </button>

      <button type="button" onClick={openOutputFolder} disabled={!hasOutput}>
        باز کردن فولدر خروجی
      </button>

      <button type="button" onClick={copyOutputPath} disabled={!outputPath}>
        کپی مسیر فایل
      </button>

      <a href={`/produce/video/${jobId}`}>به‌روزرسانی وضعیت</a>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
