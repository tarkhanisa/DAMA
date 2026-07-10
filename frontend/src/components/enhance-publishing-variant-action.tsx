"use client";

import { useState } from "react";

type EnhancePublishingVariantActionProps = {
  apiBaseUrl: string;
  variantId: string;
};

export function EnhancePublishingVariantAction({
  apiBaseUrl,
  variantId
}: EnhancePublishingVariantActionProps) {
  const [mode, setMode] = useState("dry_run");
  const [instructions, setInstructions] = useState("");
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [message, setMessage] = useState("");

  async function handleEnhance() {
    setIsEnhancing(true);
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/enhance`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            mode,
            instructions
          })
        }
      );

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در بهبود نسخه: HTTP ${response.status}`);
        return;
      }

      setMessage(
        payload.used_ai
          ? "نسخه با AI بهبود داده شد. صفحه را refresh کن."
          : "نسخه با حالت امن dry-run آماده بازبینی شد. صفحه را refresh کن."
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsEnhancing(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <label>
        حالت بهبود
        <select value={mode} onChange={(event) => setMode(event.target.value)}>
          <option value="dry_run">Dry-run امن</option>
          <option value="ollama">Ollama AI</option>
        </select>
      </label>

      <label>
        دستور تکمیلی
        <input
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
          placeholder="مثلا رسمیتر کوتاهتر مناسب تلگرام بدون ایموجی"
        />
      </label>

      <button type="button" onClick={handleEnhance} disabled={isEnhancing}>
        {isEnhancing ? "در حال بهبود..." : "بهبود نسخه"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
