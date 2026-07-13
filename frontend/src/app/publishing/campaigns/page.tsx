import { CreateMediaCampaignForm } from "../../../components/create-media-campaign-form";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { formatPersianDate, labelConnector } from "../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
};

type MediaCampaign = {
  id: string;
  project_name: string;
  source_title: string;
  preview: string;
  status: string;
  channel_ids: string[];
  media_items: Array<{ id: string; type: string; source: string }>;
  created_at: string;
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

function normalizeChannels(payload: unknown): ChannelOption[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      name: String(item.name ?? ""),
      channel_type: String(item.channel_type ?? ""),
      status: String(item.status ?? "")
    }))
    .filter((item) => item.id)
    .filter((item) => item.status !== "inactive");
}

function normalizeCampaigns(payload: unknown): MediaCampaign[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      project_name: String(item.project_name ?? ""),
      source_title: String(item.source_title ?? ""),
      preview: String(item.preview ?? ""),
      status: String(item.status ?? ""),
      channel_ids: Array.isArray(item.channel_ids) ? item.channel_ids.map(String) : [],
      media_items: Array.isArray(item.media_items)
        ? item.media_items.map((media) => {
            const value = asRecord(media);
            return {
              id: String(value.id ?? ""),
              type: String(value.type ?? ""),
              source: String(value.source ?? "")
            };
          })
        : [],
      created_at: String(item.created_at ?? "")
    }))
    .filter((item) => item.id);
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

export default async function MediaCampaignsPage() {
  const [campaignsPayload, channelsPayload] = await Promise.all([
    loadJson("/publishing/campaigns"),
    loadJson("/publishing/channels")
  ]);

  const campaigns = normalizeCampaigns(campaignsPayload);
  const channels = normalizeChannels(channelsPayload);

  const mediaCount = campaigns.reduce((total, campaign) => total + campaign.media_items.length, 0);
  const selectedChannelCount = campaigns.reduce((total, campaign) => total + campaign.channel_ids.length, 0);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="کمپین چندرسانه‌ای"
        title="کمپین‌های انتشار"
        lead="اینجا متن مادر، عکس‌ها یا ویدیوها و کانال‌های مقصد را در قالب یک کمپین ذخیره می‌کنی."
      >
        <div className="actions">
          <a href="/publishing">مرکز انتشار</a>
          <a href="/publishing/variants">نسخه‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کمپین‌ها" value={campaigns.length} helper="کمپین‌های ثبت‌شده" />
        <StatCard label="رسانه‌ها" value={mediaCount} helper="عکس/ویدیو/فایل" />
        <StatCard label="کانال‌های انتخابی" value={selectedChannelCount} helper="مقصدهای کمپین‌ها" />
        <StatCard label="کانال‌های فعال" value={channels.length} helper="قابل انتخاب" />
      </section>

      <section className="two-column">
        <CreateMediaCampaignForm apiBaseUrl={API_BASE_URL} channels={channels} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>این صفحه چه کار می‌کند؟</h2>
          </div>

          <ol className="simple-steps">
            <li>یک متن مادر برای کمپین می‌نویسی.</li>
            <li>عکس‌ها یا ویدیوهای مربوط را معرفی می‌کنی.</li>
            <li>کانال‌های مقصد را انتخاب می‌کنی.</li>
            <li>در مرحله بعد، DAMA از همین کمپین نسخه‌های کانالی می‌سازد.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست کمپین‌ها</p>
          <h2>کمپین‌های اخیر</h2>
        </div>

        <div className="campaign-grid">
          {campaigns.length > 0 ? (
            campaigns.map((campaign) => (
              <a className="campaign-card" href={`/publishing/campaigns/${campaign.id}`} key={campaign.id}>
                <div>
                  <span className={`status-badge status-${campaign.status}`}>
                    {statusLabel(campaign.status)}
                  </span>
                  <strong>{campaign.source_title}</strong>
                  <p>{campaign.preview || "بدون توضیح کوتاه"}</p>
                </div>

                <dl>
                  <div>
                    <dt>پروژه</dt>
                    <dd>{campaign.project_name || ""}</dd>
                  </div>
                  <div>
                    <dt>رسانه</dt>
                    <dd>{campaign.media_items.length}</dd>
                  </div>
                  <div>
                    <dt>کانال</dt>
                    <dd>{campaign.channel_ids.length}</dd>
                  </div>
                  <div>
                    <dt>زمان</dt>
                    <dd>{formatPersianDate(campaign.created_at)}</dd>
                  </div>
                </dl>
              </a>
            ))
          ) : (
            <p className="muted-note">هنوز کمپینی ساخته نشده است.</p>
          )}
        </div>
      </section>
    </main>
  );
}
