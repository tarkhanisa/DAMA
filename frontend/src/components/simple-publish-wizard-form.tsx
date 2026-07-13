"use client";

import { FormEvent, useMemo, useState } from "react";
import { friendlyErrorMessage, labelConnector } from "../lib/persian-copy";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
};

type SimplePublishWizardFormProps = {
  apiBaseUrl: string;
  channels: ChannelOption[];
};

export function SimplePublishWizardForm({
  apiBaseUrl,
  channels
}: SimplePublishWizardFormProps) {
  const defaultChannelIds = useMemo(
    () => channels.filter((channel) => ["wordpress", "telegram"].includes(channel.channel_type)).map((channel) => channel.id),
    [channels]
  );

  const [projectName, setProjectName] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceBody, setSourceBody] = useState("");
  const [mediaUrls, setMediaUrls] = useState("");
  const [selectedChannelIds, setSelectedChannelIds] = useState<string[]>(defaultChannelIds);
  const [message, setMessage] = useState("");
  const [campaignLink, setCampaignLink] = useState("");
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
    setCampaignLink("");

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
          media_urls: mediaUrls,
          channel_ids: selectedChannelIds,
          campaign_goal: "انتشار چندکاناله",
          notes: "created from simplified publish wizard"
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("کمپین انتشار ساخته شد. قدم بعدی: ساخت نسخه‌های مخصوص هر کانال.");
      setCampaignLink(`/publishing/campaigns/${payload.id}`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel publish-wizard-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">شروع انتشار</p>
        <h2>اول پروژه را مشخص کن</h2>
      </div>

      <label>
        این محتوا برای کدام پروژه است؟
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="مثلاً دامامدیا، گرگران، درخت و دختر، اورماشاپ..."
          required
        />
      </label>

      <label>
        عنوان انتشار
        <input
          value={sourceTitle}
          onChange={(event) => setSourceTitle(event.target.value)}
          placeholder="عنوان کوتاه این پست یا کمپین"
          required
        />
      </label>

      <label>
        توضیح اصلی
        <textarea
          value={sourceBody}
          onChange={(event) => setSourceBody(event.target.value)}
          placeholder="توضیح اصلی را اینجا بنویس. بعداً برای هر شبکه نسخه مناسب ساخته می‌شود."
          rows={7}
          required
        />
      </label>

      <label>
        عکس‌ها یا ویدیوها
        <textarea
          value={mediaUrls}
          onChange={(event) => setMediaUrls(event.target.value)}
          placeholder="هر مسیر فایل یا لینک را در یک خط بگذار. مثال: I:\DAMA\media\poster.jpg"
          rows={4}
        />
      </label>

      <div className="field-group">
        <span>کجا منتشر شود؟</span>

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
            <p className="muted-note">هنوز کانال فعالی ثبت نشده است. اول از بخش تنظیمات/انتشار کانال‌ها را بساز.</p>
          )}
        </div>
      </div>

      <p className="muted-note">
        این دکمه هنوز چیزی را منتشر نمی‌کند. فقط یک کمپین مادر می‌سازد تا در قدم بعد برای هر کانال نسخه جدا ساخته شود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      {campaignLink ? (
        <div className="actions">
          <a href={campaignLink}>مشاهده کمپین ساخته‌شده</a>
          <a href="/publishing/campaigns">همه کمپین‌ها</a>
        </div>
      ) : null}

      <button type="submit" disabled={isSaving || !projectName || !sourceTitle || !sourceBody}>
        {isSaving ? "در حال ساخت..." : "ساخت کمپین انتشار"}
      </button>
    </form>
  );
}
