"use client";

import { useState } from "react";

type TelegramPreviewTestSendActionProps = {
  apiBaseUrl: string;
  variantId: string;
  variantStatus: string;
  channelType: string;
};

export function TelegramPreviewTestSendAction({
  apiBaseUrl,
  variantId,
  variantStatus,
  channelType
}: TelegramPreviewTestSendActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [chatId, setChatId] = useState("");
  const [notes, setNotes] = useState("");
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [message, setMessage] = useState("");
  const [previewText, setPreviewText] = useState("");
  const [attemptLink, setAttemptLink] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  const canUse =
    channelType === "telegram" &&
    ["approved", "ready_for_publish", "scheduled"].includes(variantStatus);

  function payload() {
    return {
      mode,
      chat_id: chatId,
      notes,
      requested_by: "اپراتور دامامدیا",
      disable_web_page_preview: true
    };
  }

  async function handlePreview() {
    setIsPreviewing(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/telegram/preview`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload())
        }
      );

      const data = await response.json();
      setRaw(data);
      setPreviewText(data.text ?? "");

      if (!response.ok) {
        setMessage(`خطا در پیش‌نمایش تلگرام: HTTP ${response.status}`);
        return;
      }

      setMessage(data.ok ? "پیش‌نمایش تلگرام آماده است." : "این نسخه برای تلگرام هنوز مشکل دارد.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsPreviewing(false);
    }
  }

  async function handleSendTest() {
    setIsSending(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/telegram/send-test`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload())
        }
      );

      const data = await response.json();
      setRaw(data);

      const attemptId = data.attempt?.id;

      if (attemptId) {
        setAttemptLink(`/publishing/attempts/${attemptId}`);
      }

      if (!response.ok) {
        setMessage(`خطا در ارسال تست تلگرام: HTTP ${response.status}`);
        return;
      }

      const status = data.attempt?.status ?? "unknown";

      if (status === "test_sent") {
        setMessage("پیام تست تلگرام ارسال شد.");
      } else if (status === "dry_run") {
        setMessage("Dry-run انجام شد. هیچ پیامی به تلگرام ارسال نشد.");
      } else {
        setMessage(data.message ?? status);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <p className="eyebrow">تلگرام</p>
        <h2>پیش‌نمایش و ارسال تست تلگرام</h2>
      </div>

      {channelType !== "telegram" ? (
        <p className="muted-note">
          این نسخه برای تلگرام نیست؛ بنابراین ارسال تست تلگرام روی آن فعال نیست.
        </p>
      ) : null}

      {channelType === "telegram" && !canUse ? (
        <p className="muted-note">
          قبل از ارسال تست، وضعیت نسخه باید «تأیید شده» یا «آماده انتشار» باشد.
        </p>
      ) : null}

      <div className="enhance-variant-action">
        <label>
          حالت ارسال
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="dry_run">Dry-run امن</option>
            <option value="telegram">ارسال تست واقعی</option>
          </select>
        </label>

        <label>
          Chat ID / Channel
          <input
            value={chatId}
            onChange={(event) => setChatId(event.target.value)}
            placeholder="@channel_username یا chat_id"
          />
        </label>

        <label>
          یادداشت
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="مثلاً تست ارسال به کانال داخلی"
          />
        </label>

        <button
          type="button"
          onClick={handlePreview}
          disabled={isPreviewing || channelType !== "telegram"}
        >
          {isPreviewing ? "در حال ساخت پیش‌نمایش..." : "پیش‌نمایش تلگرام"}
        </button>

        <button
          type="button"
          onClick={handleSendTest}
          disabled={isSending || !canUse}
        >
          {isSending ? "در حال ارسال..." : "ارسال تست تلگرام"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}

        {attemptLink ? (
          <a className="inline-link" href={attemptLink}>
            مشاهده گزارش این تلاش
          </a>
        ) : null}
      </div>

      {previewText ? (
        <section className="panel nested-panel">
          <div className="panel-heading">
            <p className="eyebrow">Preview</p>
            <h3>متن آماده تلگرام</h3>
          </div>
          <pre className="generated-output">{previewText}</pre>
        </section>
      ) : null}

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}
    </section>
  );
}
