"use client";

import { FormEvent, useState } from "react";

type PublishingVariantOption = {
  id: string;
  variant_title: string;
  channel_name: string;
  channel_type: string;
  status: string;
};

type CreatePublishingQueueItemFormProps = {
  apiBaseUrl: string;
  variants: PublishingVariantOption[];
};

export function CreatePublishingQueueItemForm({
  apiBaseUrl,
  variants
}: CreatePublishingQueueItemFormProps) {
  const [variantId, setVariantId] = useState(variants[0]?.id ?? "");
  const [connector, setConnector] = useState(variants[0]?.channel_type ?? "telegram");
  const [mode, setMode] = useState("dry_run");
  const [chatId, setChatId] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  function handleVariantChange(nextVariantId: string) {
    setVariantId(nextVariantId);
    const selected = variants.find((variant) => variant.id === nextVariantId);

    if (selected?.channel_type) {
      setConnector(selected.channel_type);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/queue`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          variant_id: variantId,
          connector,
          mode,
          requested_by: "اپراتور دامامدیا",
          notes,
          run_payload: {
            chat_id: chatId
          }
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(payload.detail ?? `خطا: HTTP ${response.status}`);
        return;
      }

      setMessage("آیتم به صف انتشار اضافه شد. صفحه را refresh کن.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">صف انتشار</p>
        <h2>افزودن نسخه به صف</h2>
      </div>

      <label>
        نسخه آماده انتشار
        <select value={variantId} onChange={(event) => handleVariantChange(event.target.value)}>
          {variants.length > 0 ? (
            variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.variant_title || "بدون عنوان"}  {variant.channel_name || variant.channel_type}  {variant.status}
              </option>
            ))
          ) : (
            <option value="">نسخه آماده‌ای وجود ندارد</option>
          )}
        </select>
      </label>

      <label>
        Connector
        <select value={connector} onChange={(event) => setConnector(event.target.value)}>
          <option value="wordpress">WordPress</option>
          <option value="telegram">Telegram</option>
        </select>
      </label>

      <label>
        Mode
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="dry_run">Dry-run امن</option>
          <option value="wordpress">WordPress Draft واقعی</option>
          <option value="telegram">Telegram تست واقعی</option>
        </select>
      </label>

      <label>
        Chat ID برای تلگرام
        <input
          value={chatId}
          onChange={(event) => setChatId(event.target.value)}
          placeholder="@channel_username یا خالی برای default"
        />
      </label>

      <label>
        یادداشت
        <input
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="مثلاً انتشار تست یا ارسال برای بازبینی"
        />
      </label>

      <p className="muted-note">
        حالت پیش‌فرض Dry-run است. برای اجرای واقعی، connector و mode باید عمداً انتخاب شود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving || !variantId}>
        {isSaving ? "در حال افزودن..." : "افزودن به صف"}
      </button>
    </form>
  );
}
