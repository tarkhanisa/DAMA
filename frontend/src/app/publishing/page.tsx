import { PageHeader } from "../../components/page-header";
import { SimplePublishWizardForm } from "../../components/simple-publish-wizard-form";
import { StatCard } from "../../components/stat-card";
import { labelConnector } from "../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
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

export default async function PublishingHomePage() {
  const channels = normalizeChannels(await loadJson("/publishing/channels"));

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار"
        title="چه چیزی را برای کدام پروژه منتشر کنیم"
        lead="اول پروژه را مشخص کن بعد متن و رسانه را وارد کن سپس کانالهای مقصد را انتخاب کن."
      >
        <div className="actions">
          <a href="/publishing/campaigns">کمپینهای قبلی</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="قدم فعلی" value="ساخت کمپین" helper="هنوز انتشار واقعی انجام نمیشود" />
        <StatCard label="کانالهای فعال" value={channels.length} helper="قابل انتخاب برای کمپین" />
        <StatCard label="مرحله بعد" value="نسخهسازی" helper="برای هر کانال متن جدا ساخته میشود" />
        <StatCard label="انتشار" value="دستی" helper="بعد از بازبینی و صف انتشار" />
      </section>

      <section className="publish-flow-strip" aria-label="مسیر انتشار">
        <div>
          <span></span>
          <strong>پروژه</strong>
        </div>
        <div>
          <span></span>
          <strong>متن و رسانه</strong>
        </div>
        <div>
          <span></span>
          <strong>کانالها</strong>
        </div>
        <div>
          <span></span>
          <strong>نسخهسازی</strong>
        </div>
        <div>
          <span></span>
          <strong>صف انتشار</strong>
        </div>
      </section>

      <section className="two-column">
        <SimplePublishWizardForm apiBaseUrl={API_BASE_URL} channels={channels} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">کانالهای فعلی</p>
            <h2>مقصدهای قابل انتخاب</h2>
          </div>

          <div className="channel-chip-list">
            {channels.length > 0 ? (
              channels.map((channel) => (
                <span className="channel-chip" key={channel.id}>
                  {channel.name || labelConnector(channel.channel_type)}
                  <small>{labelConnector(channel.channel_type)}</small>
                </span>
              ))
            ) : (
              <p className="muted-note">هنوز کانالی ثبت نشده است.</p>
            )}
          </div>

          <div className="actions">
            <a href="/publishing/campaigns">کمپینها</a>
            <a href="/settings">تنظیمات اتصال</a>
          </div>
        </section>
      </section>
    </main>
  );
}
