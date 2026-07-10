"use client";

import { useState } from "react";

type CreateWordPressDraftActionProps = {
  apiBaseUrl: string;
  variantId: string;
  variantStatus: string;
  channelType: string;
};

export function CreateWordPressDraftAction({
  apiBaseUrl,
  variantId,
  variantStatus,
  channelType
}: CreateWordPressDraftActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [notes, setNotes] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");

  const canUse =
    channelType === "wordpress" &&
    ["approved", "ready_for_publish", "scheduled"].includes(variantStatus);

  async function handleCreateDraft() {
    setIsCreating(true);
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/wordpress/draft`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            mode,
            notes,
            requested_by: "اپراتور دامامدیا"
          })
        }
      );

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در ساخت پیش‌نویس وردپرس: HTTP ${response.status}`);
        return;
      }

      const status = payload.attempt?.status ?? "unknown";
      const link = payload.attempt?.response?.wordpress_link;

      if (status === "draft_created" && link) {
        setMessage(`پیش‌نویس وردپرس ساخته شد: ${link}`);
      } else if (status === "dry_run") {
        setMessage("Dry-run انجام شد. هیچ چیزی روی وردپرس ساخته نشد.");
      } else {
        setMessage(payload.message ?? status);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">وردپرس</p>
        <h2>ساخت پیش‌نویس وردپرس</h2>
      </div>

      {channelType !== "wordpress" ? (
        <p className="muted-note">
          این نسخه برای وردپرس نیست؛ بنابراین ساخت Draft وردپرس روی آن فعال نیست.
        </p>
      ) : null}

      {channelType === "wordpress" && !canUse ? (
        <p className="muted-note">
          قبل از ساخت پیش‌نویس وردپرس، وضعیت نسخه باید «تأیید شده» یا «آماده انتشار» باشد.
        </p>
      ) : null}

      <div className="enhance-variant-action">
        <label>
          حالت اتصال
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="wordpress">ساخت Draft واقعی در وردپرس</option>
          </select>
        </label>

        <label>
          یادداشت
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="مثلاً Draft برای بازبینی سردبیر"
          />
        </label>

        <button
          type="button"
          onClick={handleCreateDraft}
          disabled={isCreating || !canUse}
        >
          {isCreating ? "در حال انجام..." : "ساخت پیش‌نویس وردپرس"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}
      </div>

      <p className="muted-note">
        حالت Dry-run هیچ درخواستی به وردپرس نمی‌فرستد. برای اتصال واقعی باید متغیرهای محیطی وردپرس در .env تنظیم شده باشند.
      </p>
    </section>
  );
}
