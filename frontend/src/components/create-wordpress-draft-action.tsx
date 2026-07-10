"use client";

import { useState } from "react";

type CreateWordPressDraftActionProps = {
  apiBaseUrl: string;
  variantId: string;
  variantStatus: string;
  channelType: string;
};

function parseNumberList(value: string): number[] {
  return value
    .split(",")
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((item) => Number.isFinite(item));
}

export function CreateWordPressDraftAction({
  apiBaseUrl,
  variantId,
  variantStatus,
  channelType
}: CreateWordPressDraftActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [excerpt, setExcerpt] = useState("");
  const [slug, setSlug] = useState("");
  const [categories, setCategories] = useState("");
  const [tags, setTags] = useState("");
  const [seoTitle, setSeoTitle] = useState("");
  const [metaDescription, setMetaDescription] = useState("");
  const [notes, setNotes] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [attemptLink, setAttemptLink] = useState("");
  const [raw, setRaw] = useState<unknown>(null);

  const canUse =
    channelType === "wordpress" &&
    ["approved", "ready_for_publish", "scheduled"].includes(variantStatus);

  function payload() {
    return {
      mode,
      excerpt,
      slug,
      categories: parseNumberList(categories),
      tags: parseNumberList(tags),
      seo_title: seoTitle,
      meta_description: metaDescription,
      notes,
      requested_by: "اپراتور دامامدیا"
    };
  }

  async function handleValidate() {
    setIsValidating(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/wordpress/validate`,
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

      if (!response.ok) {
        setMessage(`خطا در اعتبارسنجی: HTTP ${response.status}`);
        return;
      }

      if (data.ok) {
        setMessage(
          data.can_create_real_draft
            ? "این نسخه برای Draft واقعی آماده است."
            : "این نسخه برای Dry-run آماده است؛ env وردپرس هنوز برای Draft واقعی کامل نیست."
        );
      } else {
        setMessage("این نسخه هنوز مشکل دارد.");
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsValidating(false);
    }
  }

  async function handleCreateDraft() {
    setIsCreating(true);
    setMessage("");
    setRaw(null);
    setAttemptLink("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/wordpress/draft`,
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
        setMessage(`خطا در ساخت پیش‌نویس وردپرس: HTTP ${response.status}`);
        return;
      }

      const status = data.attempt?.status ?? "unknown";
      const link = data.attempt?.response?.wordpress_link;

      if (status === "draft_created" && link) {
        setMessage(`پیش‌نویس وردپرس ساخته شد.`);
      } else if (status === "dry_run") {
        setMessage("Dry-run انجام شد. هیچ چیزی روی وردپرس ساخته نشد.");
      } else {
        setMessage(data.message ?? status);
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
          خلاصه / Excerpt
          <input
            value={excerpt}
            onChange={(event) => setExcerpt(event.target.value)}
            placeholder="خلاصه کوتاه برای وردپرس"
          />
        </label>

        <label>
          Slug
          <input
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
            placeholder="example-post-slug"
          />
        </label>

        <label>
          Categories ID
          <input
            value={categories}
            onChange={(event) => setCategories(event.target.value)}
            placeholder="مثلاً 3,7"
          />
        </label>

        <label>
          Tags ID
          <input
            value={tags}
            onChange={(event) => setTags(event.target.value)}
            placeholder="مثلاً 12,18"
          />
        </label>

        <label>
          SEO Title
          <input
            value={seoTitle}
            onChange={(event) => setSeoTitle(event.target.value)}
            placeholder="عنوان پیشنهادی سئو"
          />
        </label>

        <label>
          Meta Description
          <input
            value={metaDescription}
            onChange={(event) => setMetaDescription(event.target.value)}
            placeholder="توضیح متا برای سئو"
          />
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
          onClick={handleValidate}
          disabled={isValidating || !canUse}
        >
          {isValidating ? "در حال بررسی..." : "اعتبارسنجی Draft"}
        </button>

        <button
          type="button"
          onClick={handleCreateDraft}
          disabled={isCreating || !canUse}
        >
          {isCreating ? "در حال انجام..." : "ساخت پیش‌نویس وردپرس"}
        </button>

        {message ? <p className="form-message">{message}</p> : null}

        {attemptLink ? (
          <a className="inline-link" href={attemptLink}>
            مشاهده گزارش این تلاش
          </a>
        ) : null}
      </div>

      {raw ? (
        <details>
          <summary>پاسخ خام</summary>
          <pre className="json-block">{JSON.stringify(raw, null, 2)}</pre>
        </details>
      ) : null}

      <p className="muted-note">
        SEO title و meta description فعلاً در گزارش تلاش ذخیره می‌شوند. ارسال مستقیم به افزونه‌های سئو فقط وقتی فعال می‌شود که DAMA_WORDPRESS_SEND_SEO_META را عمداً فعال کنی.
      </p>
    </section>
  );
}
