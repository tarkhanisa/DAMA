import { CreatePublishingChannelForm } from "../../components/create-publishing-channel-form";
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type PublishingChannel = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
  target_url?: string;
  public_handle?: string;
  notes?: string;
  secret_configured?: boolean;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeChannels(payload: unknown): PublishingChannel[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : Array.isArray(record.items)
      ? record.items
      : [];

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        name: String(value.name ?? "کانال بدون نام"),
        channel_type: String(value.channel_type ?? "manual"),
        status: String(value.status ?? "not_configured"),
        target_url: typeof value.target_url === "string" ? value.target_url : "",
        public_handle:
          typeof value.public_handle === "string" ? value.public_handle : "",
        notes: typeof value.notes === "string" ? value.notes : "",
        secret_configured: Boolean(value.secret_configured)
      };
    })
    .filter((item) => item.id);
}

async function loadChannels(): Promise<PublishingChannel[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/channels`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return [];
    }

    return normalizeChannels(await response.json());
  } catch {
    return [];
  }
}

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

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    not_configured: "تنظیم‌نشده",
    configured: "تنظیم‌شده",
    ready: "آماده",
    needs_review: "نیازمند بررسی",
    disabled: "غیرفعال",
    failed: "خطادار"
  };

  return labels[status] ?? status;
}

export default async function PublishingPage() {
  const channels = await loadChannels();
  const configuredCount = channels.filter((item) =>
    ["configured", "ready"].includes(item.status)
  ).length;
  const needsReviewCount = channels.filter((item) =>
    ["not_configured", "needs_review", "failed"].includes(item.status)
  ).length;

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار چندکاناله"
        title="کانال‌های انتشار"
        lead="اینجا مقصدهای انتشار را تعریف می‌کنی. در این مرحله هنوز انتشار واقعی انجام نمی‌شود؛ فقط نقشه کانال‌ها ساخته می‌شود."
      >
        <div className="actions">
          <a href="/generate">تولید محتوا</a>
          <a href="/content-assets">محتواها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="همه کانال‌ها" value={channels.length} helper="مقصدهای تعریف‌شده" />
        <StatCard label="آماده‌تر" value={configuredCount} helper="تنظیم‌شده یا آماده" />
        <StatCard label="نیازمند بررسی" value={needsReviewCount} helper="هنوز برای انتشار آماده نیستند" />
        <StatCard label="انتشار واقعی" value="بعداً" helper="در Releaseهای بعدی فعال می‌شود" />
      </section>

      <section className="two-column">
        <CreatePublishingChannelForm apiBaseUrl={API_BASE_URL} />

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">نقشه راه</p>
            <h2>بعد از این مرحله چه می‌شود؟</h2>
          </div>

          <ol className="simple-steps">
            <li>اول کانال‌ها را تعریف می‌کنیم.</li>
            <li>بعد برای هر محتوا نسخه مخصوص هر کانال ساخته می‌شود.</li>
            <li>بعد پیش‌نمایش و تأیید انسانی اضافه می‌شود.</li>
            <li>بعد اتصال واقعی وردپرس و تلگرام را فعال می‌کنیم.</li>
            <li>بعد صف انتشار و گزارش خطا ساخته می‌شود.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست کانال‌ها</p>
          <h2>مقصدهای انتشار</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>نام</th>
                <th>نوع</th>
                <th>وضعیت</th>
                <th>آدرس / handle</th>
                <th>Secret</th>
              </tr>
            </thead>
            <tbody>
              {channels.length > 0 ? (
                channels.map((channel) => (
                  <tr key={channel.id}>
                    <td>{channel.name}</td>
                    <td>{channelTypeLabel(channel.channel_type)}</td>
                    <td>
                      <span className={`status-badge status-${channel.status}`}>
                        {statusLabel(channel.status)}
                      </span>
                    </td>
                    <td>{channel.public_handle || channel.target_url || ""}</td>
                    <td>{channel.secret_configured ? "تنظیم شده" : "تنظیم نشده"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>هنوز کانالی تعریف نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
