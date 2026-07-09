"use client";

import { FormEvent, useState } from "react";

type CreatePublishingChannelFormProps = {
  apiBaseUrl: string;
};

const channelTypes = [
  { value: "wordpress", label: "وردپرس" },
  { value: "telegram", label: "تلگرام" },
  { value: "instagram", label: "اینستاگرام" },
  { value: "linkedin", label: "لینکدین" },
  { value: "whatsapp", label: "واتساپ" },
  { value: "bale", label: "بله" },
  { value: "eitaa", label: "ایتا" },
  { value: "manual", label: "دستی / فقط بازبینی" }
];

export function CreatePublishingChannelForm({
  apiBaseUrl
}: CreatePublishingChannelFormProps) {
  const [name, setName] = useState("");
  const [channelType, setChannelType] = useState("wordpress");
  const [targetUrl, setTargetUrl] = useState("");
  const [publicHandle, setPublicHandle] = useState("");
  const [notes, setNotes] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/channels`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name,
          channel_type: channelType,
          target_url: targetUrl,
          public_handle: publicHandle,
          notes,
          status: "not_configured"
        })
      });

      if (!response.ok) {
        setMessage(`خطا در ساخت کانال: HTTP ${response.status}`);
        return;
      }

      setMessage("کانال ساخته شد. برای دیدن لیست، صفحه را refresh کن.");
      setName("");
      setTargetUrl("");
      setPublicHandle("");
      setNotes("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">کانال جدید</p>
        <h2>مسیر انتشار را تعریف کن</h2>
      </div>

      <label>
        نام کانال
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="مثلاً سایت گرگران، تلگرام اورماشاپ، اینستاگرام دامامدیا"
        />
      </label>

      <label>
        نوع کانال
        <select
          value={channelType}
          onChange={(event) => setChannelType(event.target.value)}
        >
          {channelTypes.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        آدرس یا مقصد عمومی
        <input
          value={targetUrl}
          onChange={(event) => setTargetUrl(event.target.value)}
          placeholder="مثلاً https://example.com یا @channel"
        />
      </label>

      <label>
        شناسه عمومی / handle
        <input
          value={publicHandle}
          onChange={(event) => setPublicHandle(event.target.value)}
          placeholder="مثلاً @damamedia یا نام صفحه"
        />
      </label>

      <label>
        توضیحات
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={4}
          placeholder="این کانال برای چه پروژه‌ای است؟ چه محدودیت‌هایی دارد؟"
        />
      </label>

      <p className="muted-note">
        در این مرحله token، password یا secret وارد نکن. این بخش فقط رجیستری امن کانال‌هاست.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving}>
        {isSaving ? "در حال ذخیره..." : "ساخت کانال"}
      </button>
    </form>
  );
}
