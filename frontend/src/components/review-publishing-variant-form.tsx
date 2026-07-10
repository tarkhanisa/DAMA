"use client";

import { FormEvent, useState } from "react";

type ReviewPublishingVariantFormProps = {
  apiBaseUrl: string;
  variantId: string;
  initialTitle: string;
  initialBody: string;
  initialStatus: string;
  initialNotes?: string;
};

export function ReviewPublishingVariantForm({
  apiBaseUrl,
  variantId,
  initialTitle,
  initialBody,
  initialStatus,
  initialNotes = ""
}: ReviewPublishingVariantFormProps) {
  const [variantTitle, setVariantTitle] = useState(initialTitle);
  const [variantBody, setVariantBody] = useState(initialBody);
  const [status, setStatus] = useState(initialStatus || "ready_for_review");
  const [reviewNotes, setReviewNotes] = useState(initialNotes);
  const [reviewedBy, setReviewedBy] = useState("اپراتور دامامدیا");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/review`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            variant_title: variantTitle,
            variant_body: variantBody,
            status,
            review_notes: reviewNotes,
            reviewed_by: reviewedBy
          })
        }
      );

      if (!response.ok) {
        setMessage(`خطا در ثبت بازبینی: HTTP ${response.status}`);
        return;
      }

      setMessage("بازبینی ذخیره شد. صفحه را refresh کن تا وضعیت جدید را ببینی.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">بازبینی انسانی</p>
        <h2>نسخه نهایی این کانال را تأیید یا رد کن</h2>
      </div>

      <label>
        عنوان نسخه
        <input
          value={variantTitle}
          onChange={(event) => setVariantTitle(event.target.value)}
        />
      </label>

      <label>
        متن نسخه
        <textarea
          value={variantBody}
          onChange={(event) => setVariantBody(event.target.value)}
          rows={14}
        />
      </label>

      <label>
        وضعیت بازبینی
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="draft">پیشنویس</option>
          <option value="ready_for_review">آماده بازبینی</option>
          <option value="approved">تأیید شده</option>
          <option value="ready_for_publish">آماده انتشار</option>
          <option value="rejected">رد شده</option>
        </select>
      </label>

      <label>
        بازبین
        <input
          value={reviewedBy}
          onChange={(event) => setReviewedBy(event.target.value)}
        />
      </label>

      <label>
        یادداشت بازبینی
        <textarea
          value={reviewNotes}
          onChange={(event) => setReviewNotes(event.target.value)}
          rows={4}
          placeholder="مثلا متن مناسب است اما قبل از انتشار نیاز به تصویر دارد."
        />
      </label>

      <p className="muted-note">
        هنوز انتشار واقعی انجام نمیشود. وضعیت آماده انتشار فقط برای مرحله بعدی صف انتشار استفاده میشود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving}>
        {isSaving ? "در حال ذخیره..." : "ذخیره بازبینی"}
      </button>
    </form>
  );
}
