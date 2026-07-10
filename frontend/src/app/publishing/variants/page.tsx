import { CreatePublishingVariantsForm } from "../../../components/create-publishing-variants-form";
import { EnhancePublishingVariantAction } from "../../../components/enhance-publishing-variant-action";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

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
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

async function getJson(endpoint: string): Promise<unknown> {
  const response = await fetch(endpoint, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

function normalizeAssets(payload: unknown): ContentAsset[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.items ?? record.assets ?? record.content_assets ?? record.data);

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        title: String(value.title ?? value.name ?? "محتوای بدون عنوان"),
        body: String(value.body ?? value.content ?? value.response ?? value.text ?? ""),
        content_type:
          typeof value.content_type === "string" ? value.content_type : undefined,
        status: typeof value.status === "string" ? value.status : undefined
      };
    })
    .filter((asset) => asset.id && asset.body);
}

function normalizeChannels(payload: unknown): PublishingChannel[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload) ? payload : asArray(record.items);

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        name: String(value.name ?? "کانال بدون نام"),
        channel_type: String(value.channel_type ?? "manual"),
        status: String(value.status ?? "not_configured")
      };
    })
    .filter((channel) => channel.id);
}

function normalizeVariants(payload: unknown): PublishingVariant[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload) ? payload : asArray(record.items);

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        content_asset_id: String(value.content_asset_id ?? ""),
        channel_id: String(value.channel_id ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? "manual"),
        variant_title: String(value.variant_title ?? ""),
        variant_body: String(value.variant_body ?? ""),
        status: String(value.status ?? "draft")
      };
    })
    .filter((variant) => variant.id);
}

async function loadAssets(): Promise<ContentAsset[]> {
  try {
    return normalizeAssets(await getJson(`${API_BASE_URL}/content-assets`));
  } catch {
    return [];
  }
}

async function loadChannels(): Promise<PublishingChannel[]> {
  try {
    return normalizeChannels(await getJson(`${API_BASE_URL}/publishing/channels`));
  } catch {
    return [];
  }
}

async function loadVariants(): Promise<PublishingVariant[]> {
  try {
    return normalizeVariants(await getJson(`${API_BASE_URL}/publishing/variants`));
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

export default async function PublishingVariantsPage() {
  const [assets, channels, variants] = await Promise.all([
    loadAssets(),
    loadChannels(),
    loadVariants()
  ]);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="نسخهسازی انتشار"
        title="تبدیل محتوای مادر به نسخههای کانالی"
        lead="یک محتوای ذخیرهشده را انتخاب کن و برای کانالهای مختلف نسخه مناسب همان کانال بساز."
      >
        <div className="actions">
          <a href="/publishing">کانالهای انتشار</a>
          <a href="/generate">تولید محتوا</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="محتواهای قابل استفاده" value={assets.length} helper="Content Assets دارای متن" />
        <StatCard label="کانالها" value={channels.length} helper="مقصدهای تعریفشده" />
        <StatCard label="نسخههای ساختهشده" value={variants.length} helper="Publishing Variants" />
        <StatCard label="انتشار واقعی" value="بعدا" helper="فعلا فقط پیشنویس کانالی" />
      </section>

      <CreatePublishingVariantsForm
        apiBaseUrl={API_BASE_URL}
        assets={assets}
        channels={channels}
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">آرشیو نسخهها</p>
          <h2>آخرین نسخههای کانالی</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>عنوان</th>
                <th>کانال</th>
                <th>نوع</th>
                <th>وضعیت</th>
                <th>اقدام</th>
              </tr>
            </thead>
            <tbody>
              {variants.length > 0 ? (
                variants.slice(0, 20).map((variant) => (
                  <tr key={variant.id}>
                    <td>{variant.variant_title}</td>
                    <td>{variant.channel_name}</td>
                    <td>{channelTypeLabel(variant.channel_type)}</td>
                    <td>
                      <span className={`status-badge status-${variant.status}`}>
                        {variant.status}
                      </span>
                    </td>
                    <td>
                      <EnhancePublishingVariantAction
                        apiBaseUrl={API_BASE_URL}
                        variantId={variant.id}
                      />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>هنوز نسخهای ساخته نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
