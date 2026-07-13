import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";
import { formatPersianDate, labelConnector, shortId } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type Props = {
  params: Promise<{
    campaignId: string;
  }>;
};

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getItems(payload: unknown): Record<string, unknown>[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return source.map(asRecord);
}

async function loadJson(path: string): Promise<unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return await response.json();
  } catch {
    return {};
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "پیش‌نویس",
    ready: "آماده نسخه‌سازی",
    variant_planned: "نسخه‌سازی شده",
    queued: "وارد صف شده",
    published: "منتشر شده",
    archived: "آرشیو شده"
  };

  return labels[status] ?? "پیش‌نویس";
}

function mediaTypeLabel(type: string): string {
  if (type === "image") {
    return "تصویر";
  }

  if (type === "video") {
    return "ویدیو";
  }

  if (type === "document") {
    return "فایل";
  }

  return "رسانه";
}

export default async function MediaCampaignDetailPage({ params }: Props) {
  const { campaignId } = await params;

  const [campaignPayload, channelsPayload] = await Promise.all([
    loadJson(`/publishing/campaigns/${campaignId}`),
    loadJson("/publishing/channels")
  ]);

  const campaign = asRecord(campaignPayload);
  const mediaItems = Array.isArray(campaign.media_items)
    ? campaign.media_items.map(asRecord)
    : [];
  const channelIds = Array.isArray(campaign.channel_ids)
    ? campaign.channel_ids.map(String)
    : [];

  const channels: ChannelOption[] = getItems(channelsPayload)
    .map((item) => ({
      id: String(item.id ?? ""),
      name: String(item.name ?? ""),
      channel_type: String(item.channel_type ?? "")
    }))
    .filter((item) => item.id);

  const selectedChannels = channels.filter((channel) => channelIds.includes(channel.id));

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="جزئیات کمپین"
        title={String(campaign.source_title ?? "کمپین")}
        lead={String(campaign.preview ?? "کمپین چندرسانه‌ای برای نسخه‌سازی و انتشار چندکاناله.")}
      >
        <div className="actions">
          <a href="/publishing/campaigns">بازگشت به کمپین‌ها</a>
          <a href="/publishing/variants">نسخه‌سازی</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(String(campaign.status ?? ""))} helper={`شناسه: ${shortId(campaignId)}`} />
        <StatCard label="رسانه‌ها" value={mediaItems.length} helper="عکس، ویدیو یا فایل" />
        <StatCard label="کانال‌های مقصد" value={selectedChannels.length} helper="برای نسخه‌سازی بعدی" />
        <StatCard label="زمان ساخت" value={formatPersianDate(String(campaign.created_at ?? ""))} helper={String(campaign.project_name ?? "")} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">متن مادر</p>
            <h2>محتوای اصلی کمپین</h2>
          </div>

          <div className="generated-output">
            <h3>{String(campaign.source_title ?? "بدون عنوان")}</h3>
            <p>{String(campaign.source_body ?? "بدون متن")}</p>
          </div>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">قدم بعدی</p>
            <h2>بعد از ساخت کمپین</h2>
          </div>

          <ol className="simple-steps">
            <li>در مرحله بعد، برای کانال‌های انتخاب‌شده نسخه مخصوص ساخته می‌شود.</li>
            <li>هر نسخه را بازبینی و تأیید می‌کنی.</li>
            <li>بعد نسخه‌ها وارد صف انتشار می‌شوند.</li>
            <li>انتشار واقعی همچنان دستی و کنترل‌شده خواهد بود.</li>
          </ol>
        </section>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">رسانه‌ها</p>
            <h2>عکس‌ها و ویدیوهای کمپین</h2>
          </div>

          <div className="media-list">
            {mediaItems.length > 0 ? (
              mediaItems.map((item) => (
                <div className="media-row" key={String(item.id ?? item.source)}>
                  <span>{mediaTypeLabel(String(item.type ?? ""))}</span>
                  <code>{String(item.source ?? "")}</code>
                </div>
              ))
            ) : (
              <p className="muted-note">برای این کمپین هنوز رسانه‌ای ثبت نشده است.</p>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">مقصدها</p>
            <h2>کانال‌های انتخاب‌شده</h2>
          </div>

          <div className="channel-chip-list">
            {selectedChannels.length > 0 ? (
              selectedChannels.map((channel) => (
                <span className="channel-chip" key={channel.id}>
                  {channel.name || labelConnector(channel.channel_type)}
                  <small>{labelConnector(channel.channel_type)}</small>
                </span>
              ))
            ) : (
              <p className="muted-note">هنوز کانالی برای این کمپین انتخاب نشده است.</p>
            )}
          </div>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی کمپین</summary>
          <pre className="json-block">{JSON.stringify(campaign, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
