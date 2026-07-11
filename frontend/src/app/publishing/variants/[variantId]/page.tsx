import { ErrorPanel } from "../../../../components/error-panel";
import { PageHeader } from "../../../../components/page-header";
import { CreateWordPressDraftAction } from "../../../../components/create-wordpress-draft-action";
import { TelegramPreviewTestSendAction } from "../../../../components/telegram-preview-test-send-action";
import { ReviewPublishingVariantForm } from "../../../../components/review-publishing-variant-form";
import { StatCard } from "../../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type VariantDetailPageProps = {
  params: Promise<{
    variantId: string;
  }>;
};

type PublishingVariant = {
  id: string;
  content_asset_id: string;
  channel_id: string;
  channel_name: string;
  channel_type: string;
  source_title: string;
  source_body: string;
  variant_title: string;
  variant_body: string;
  status: string;
  adaptation_mode?: string;
  adaptation_notes?: string[];
  review_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_history?: Array<Record<string, string>>;
};

async function loadVariant(variantId: string): Promise<PublishingVariant | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/variants/${variantId}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as PublishingVariant;
  } catch {
    return null;
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
    draft: "پیشنویس",
    ready_for_review: "آماده بازبینی",
    approved: "تأیید شده",
    ready_for_publish: "آماده انتشار",
    rejected: "رد شده",
    scheduled: "زمانبندیشده",
    published: "منتشرشده",
    failed: "خطادار"
  };

  return labels[status] ?? status;
}

export default async function PublishingVariantDetailPage({
  params
}: VariantDetailPageProps) {
  const { variantId } = await params;
  const variant = await loadVariant(variantId);

  if (!variant) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="نسخه انتشار"
          title="نسخه پیدا نشد"
          message="این نسخه کانالی در بکاند پیدا نشد."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="بازبینی نسخه انتشار"
        title={variant.variant_title || "نسخه بدون عنوان"}
        lead="اینجا متن مخصوص این کانال را با متن مادر مقایسه میکنی و وضعیت بازبینی را ثبت میکنی."
      >
        <div className="actions">
          <a href="/publishing/variants">بازگشت به نسخهسازی</a>
          <a href="/publishing">کانالها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کانال" value={variant.channel_name || ""} helper={channelTypeLabel(variant.channel_type)} />
        <StatCard label="وضعیت" value={statusLabel(variant.status)} helper="وضعیت بازبینی" />
        <StatCard label="روش آمادهسازی" value={variant.adaptation_mode || "rule_based"} helper="rule-based / AI / dry-run" />
        <StatCard label="بازبین" value={variant.reviewed_by || ""} helper={variant.reviewed_at || "هنوز بازبینی نشده"} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">متن مادر</p>
            <h2>{variant.source_title || "محتوای اصلی"}</h2>
          </div>

          <pre className="generated-output">{variant.source_body || "متن مادر ثبت نشده است."}</pre>
        </section>

        <ReviewPublishingVariantForm
          apiBaseUrl={API_BASE_URL}
          variantId={variant.id}
          initialTitle={variant.variant_title}
          initialBody={variant.variant_body}
          initialStatus={variant.status}
          initialNotes={variant.review_notes}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشتها</p>
          <h2>توضیحات آمادهسازی و بازبینی</h2>
        </div>

        <div className="two-column">
          <div>
            <h3>یادداشتهای آمادهسازی</h3>
            {variant.adaptation_notes?.length ? (
              <ul className="note-list">
                {variant.adaptation_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : (
              <p className="muted-note">یادداشتی ثبت نشده است.</p>
            )}
          </div>

          <div>
            <h3>تاریخچه بازبینی</h3>
            {variant.review_history?.length ? (
              <ul className="note-list">
                {variant.review_history.map((item, index) => (
                  <li key={`${item.reviewed_at}-${index}`}>
                    {statusLabel(item.status ?? "")}  {item.reviewed_by ?? "بازبین"}  {item.reviewed_at ?? ""}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted-note">هنوز بازبینی ثبت نشده است.</p>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
