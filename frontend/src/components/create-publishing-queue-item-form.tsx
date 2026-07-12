"use client";

import { FormEvent, useState } from "react";
import { friendlyErrorMessage, labelConnector, labelMode } from "../lib/persian-copy";

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
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("آیتم با موفقیت به صف انتشار اضافه شد. برای دیدن آن صفحه را تازه‌سازی کن.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">افزودن به صف</p>
        <h2>یک نسخه را برای انتشار آماده کن</h2>
      </div>

      <label>
        نسخه آماده انتشار
        <select value={variantId} onChange={(event) => handleVariantChange(event.target.value)}>
          {variants.length > 0 ? (
            variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.variant_title || "بدون عنوان"} — {variant.channel_name || labelConnector(variant.channel_type)}
              </option>
            ))
          ) : (
            <option value="">فعلاً نسخه آماده‌ای وجود ندارد</option>
          )}
        </select>
      </label>

      <label>
        مقصد انتشار
        <select value={connector} onChange={(event) => setConnector(event.target.value)}>
          <option value="wordpress">{labelConnector("wordpress")}</option>
          <option value="telegram">{labelConnector("telegram")}</option>
        </select>
      </label>

      <label>
        نوع اجرا
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="dry_run">{labelMode("dry_run")}</option>
          <option value="wordpress">{labelMode("wordpress")}</option>
          <option value="telegram">{labelMode("telegram")}</option>
        </select>
      </label>

      <label>
        شناسه گفت‌وگوی تلگرام
        <input
          value={chatId}
          onChange={(event) => setChatId(event.target.value)}
          placeholder="مثلاً @channel_username؛ اگر تنظیم پیش‌فرض داری، خالی بگذار"
        />
      </label>

      <label>
        یادداشت کوتاه
        <input
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="مثلاً: تست قبل از انتشار"
        />
      </label>

      <p className="muted-note">
        پیشنهاد امن: همیشه اول «اجرای آزمایشی امن» را انجام بده، بعد اجرای واقعی.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving || !variantId}>
        {isSaving ? "در حال افزودن..." : "افزودن به صف انتشار"}
      </button>
    </form>
  );
}
