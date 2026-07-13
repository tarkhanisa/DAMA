"use client";

import { FormEvent, useMemo, useState } from "react";
import { friendlyErrorMessage, labelConnector } from "../lib/persian-copy";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
};

type CreateMediaCampaignFormProps = {
  apiBaseUrl: string;
  channels: ChannelOption[];
};

export function CreateMediaCampaignForm({
  apiBaseUrl,
  channels
}: CreateMediaCampaignFormProps) {
  const defaultChannelIds = useMemo(
    () => channels.filter((channel) => ["wordpress", "telegram"].includes(channel.channel_type)).map((channel) => channel.id),
    [channels]
  );

  const [projectName, setProjectName] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceBody, setSourceBody] = useState("");
  const [campaignGoal, setCampaignGoal] = useState("");
  const [mediaUrls, setMediaUrls] = useState("");
  const [selectedChannelIds, setSelectedChannelIds] = useState<string[]>(defaultChannelIds);
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  function toggleChannel(channelId: string) {
    setSelectedChannelIds((current) =>
      current.includes(channelId)
        ? current.filter((item) => item !== channelId)
        : [...current, channelId]
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/campaigns`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          source_title: sourceTitle,
          source_body: sourceBody,
          campaign_goal: campaignGoal,
          media_urls: mediaUrls,
          channel_ids: selectedChannelIds,
          notes: "created from media campaign composer"
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("کمپین چندرسانه‌ای ساخته شد. صفحه را تازه‌سازی کن یا وارد جزئیات کمپین شو.");
      setProjectName("");
      setSourceTitle("");
      setSourceBody("");
      setCampaignGoal("");
      setMediaUrls("");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">کمپین مادر</p>
        <h2>ساخت کمپین چندرسانه‌ای</h2>
      </div>

      <label>
        نام پروژه
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="مثلاً دامامدیا، گرگران، اورماشاپ..."
        />
      </label>

      <label>
        عنوان کمپین
        <input
          value={sourceTitle}
          onChange={(event) => setSourceTitle(event.target.value)}
          placeholder="عنوانی که بعداً برای نسخه‌های کانالی استفاده می‌شود"
          required
        />
      </label>

      <label>
        متن مادر
        <textarea
          value={sourceBody}
          onChange={(event) => setSourceBody(event.target.value)}
          placeholder="توضیح اصلی کمپین را اینجا بنویس. DAMA بعداً از این متن نسخه مخصوص هر شبکه را می‌سازد."
          rows={8}
          required
        />
      </label>

      <label>
        هدف کمپین
        <input
          value={campaignGoal}
          onChange={(event) => setCampaignGoal(event.target.value)}
          placeholder="مثلاً معرفی پروژه، جذب مخاطب، اطلاع‌رسانی، فروش..."
        />
      </label>

      <label>
        عکس‌ها یا ویدیوها
        <textarea
          value={mediaUrls}
          onChange={(event) => setMediaUrls(event.target.value)}
          placeholder="هر مسیر فایل یا لینک را در یک خط بگذار. مثال: I:\DAMA\media\poster.jpg"
          rows={5}
        />
      </label>

      <div className="field-group">
        <span>کانال‌های مقصد</span>

        <div className="channel-checkbox-grid">
          {channels.length > 0 ? (
            channels.map((channel) => (
              <label className="checkbox-card" key={channel.id}>
                <input
                  type="checkbox"
                  checked={selectedChannelIds.includes(channel.id)}
                  onChange={() => toggleChannel(channel.id)}
                />
                <strong>{channel.name || labelConnector(channel.channel_type)}</strong>
                <small>{labelConnector(channel.channel_type)}</small>
              </label>
            ))
          ) : (
            <p className="muted-note">هنوز کانالی ثبت نشده است. از بخش انتشار، کانال‌ها را بساز.</p>
          )}
        </div>
      </div>

      <p className="muted-note">
        این مرحله هنوز چیزی را منتشر نمی‌کند. فقط کمپین مادر را برای نسخه‌سازی و صف انتشار آماده می‌کند.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving || !sourceTitle || !sourceBody}>
        {isSaving ? "در حال ساخت..." : "ساخت کمپین"}
      </button>
    </form>
  );
}
