"use client";

import { FormEvent, useMemo, useState } from "react";

type ContentAsset = {
  id: string;
  title: string;
  body: string;
  content_type?: string;
  status?: string;
};

type PublishingChannel = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
};

type PublishingVariant = {
  id: string;
  content_asset_id: string;
  channel_id: string;
  channel_name: string;
  channel_type: string;
  variant_title: string;
  variant_body: string;
  status: string;
  adaptation_mode: string;
  adaptation_notes: string[];
};

type CreatePublishingVariantsFormProps = {
  apiBaseUrl: string;
  assets: ContentAsset[];
  channels: PublishingChannel[];
};

function channelTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    wordpress: "وردپرس",
    telegram: "تلگرام",
    instagram: "اینستاگرام",
    linkedin: "لینکدین",
    whatsapp: "واتساپ",
    bale: "بله",
    eitaa: "ایتا",
    manual: "دستی"
  };

  return labels[type] ?? type;
}

export function CreatePublishingVariantsForm({
  apiBaseUrl,
  assets,
  channels
}: CreatePublishingVariantsFormProps) {
  const [assetId, setAssetId] = useState(assets[0]?.id ?? "");
  const [selectedChannelIds, setSelectedChannelIds] = useState<string[]>(
    channels.slice(0, 3).map((channel) => channel.id)
  );
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [createdVariants, setCreatedVariants] = useState<PublishingVariant[]>([]);

  const selectedAsset = useMemo(
    () => assets.find((asset) => asset.id === assetId),
    [assetId, assets]
  );

  function toggleChannel(channelId: string) {
    setSelectedChannelIds((current) =>
      current.includes(channelId)
        ? current.filter((item) => item !== channelId)
        : [...current, channelId]
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedAsset) {
      setMessage("اول یک محتوای مادر انتخاب کن.");
      return;
    }

    if (selectedChannelIds.length === 0) {
      setMessage("حداقل یک کانال انتشار انتخاب کن.");
      return;
    }

    setIsCreating(true);
    setMessage("");
    setCreatedVariants([]);

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/variants/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content_asset_id: selectedAsset.id,
          source_title: selectedAsset.title,
          source_body: selectedAsset.body,
          channel_ids: selectedChannelIds
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در ساخت نسخهها: HTTP ${response.status}`);
        return;
      }

      setCreatedVariants(Array.isArray(payload.items) ? payload.items : []);
      setMessage(`${payload.created ?? 0} نسخه کانالی ساخته شد.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="generation-grid">
      <form className="panel generation-form" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <p className="eyebrow">نسخهسازی کانالی</p>
          <h2>محتوا را برای کانالها آماده کن</h2>
        </div>

        <label>
          محتوای مادر
          <select value={assetId} onChange={(event) => setAssetId(event.target.value)}>
            {assets.length > 0 ? (
              assets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.title}
                </option>
              ))
            ) : (
              <option value="">محتوایی پیدا نشد</option>
            )}
          </select>
        </label>

        <div className="channel-checkbox-list">
          <strong>کانالهای مقصد</strong>

          {channels.length > 0 ? (
            channels.map((channel) => (
              <label key={channel.id} className="checkbox-row">
                <input
                  type="checkbox"
                  checked={selectedChannelIds.includes(channel.id)}
                  onChange={() => toggleChannel(channel.id)}
                />
                <span>
                  {channel.name}  {channelTypeLabel(channel.channel_type)}
                </span>
              </label>
            ))
          ) : (
            <p className="muted-note">
              هنوز کانالی تعریف نشده. اول از صفحه انتشار کانال بساز.
            </p>
          )}
        </div>

        <p className="muted-note">
          این مرحله هنوز منتشر نمیکند فقط نسخههای مخصوص هر کانال را برای بازبینی میسازد.
        </p>

        {message ? <p className="form-message">{message}</p> : null}

        <button type="submit" disabled={isCreating || assets.length === 0 || channels.length === 0}>
          {isCreating ? "در حال ساخت نسخهها..." : "ساخت نسخههای کانالی"}
        </button>
      </form>

      <section className="panel generation-output">
        <div className="panel-heading">
          <p className="eyebrow">پیشنمایش</p>
          <h2>نسخههای ساختهشده</h2>
        </div>

        {createdVariants.length > 0 ? (
          <div className="variant-preview-list">
            {createdVariants.map((variant) => (
              <article key={variant.id} className="variant-preview-card">
                <div className="variant-preview-header">
                  <strong>
                    {variant.channel_name}  {channelTypeLabel(variant.channel_type)}
                  </strong>
                  <span className={`status-badge status-${variant.status}`}>
                    {variant.status}
                  </span>
                </div>

                <h3>{variant.variant_title}</h3>
                <pre className="generated-output">{variant.variant_body}</pre>

                {variant.adaptation_notes?.length > 0 ? (
                  <ul className="note-list">
                    {variant.adaptation_notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <div className="quality-help">
            <h3>این مرحله چه میکند</h3>
            <p>
              یک محتوای مادر را انتخاب میکنی و سیستم برای هر کانال یک نسخه جدا میسازد.
            </p>
            <ul>
              <li>وردپرس: متن کاملتر و مناسب پیشنویس سایت</li>
              <li>تلگرام: پاراگرافهای کوتاهتر</li>
              <li>اینستاگرام: کپشن کوتاهتر</li>
              <li>لینکدین: نسخه رسمیتر</li>
              <li>واتساپ: نسخه کوتاه و مستقیم</li>
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
