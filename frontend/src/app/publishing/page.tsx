import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function PublishingHomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار"
        title="مرکز ساده انتشار"
        lead="از اینجا کمپین مادر می‌سازی، نسخه کانالی آماده می‌کنی، وارد صف می‌کنی و نتیجه را می‌بینی."
      >
        <div className="actions">
          <a href="/publishing/campaigns">کمپین‌ها</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کمپین‌ها" value="جدید" helper="متن + رسانه + مقصدها" />
        <StatCard label="نسخه‌ها" value="کانالی" helper="متناسب با هر شبکه" />
        <StatCard label="صف انتشار" value="دستی" helper="امن و کنترل‌شده" />
        <StatCard label="گزارش‌ها" value="ثبت کامل" helper="هر اجرا یک گزارش" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/publishing/campaigns">
          <span></span>
          <strong>کمپین چندرسانه‌ای</strong>
          <p>متن مادر، عکس/ویدیو و کانال‌های مقصد را یکجا تعریف کن.</p>
        </a>

        <a className="operator-card" href="/publishing/variants">
          <span></span>
          <strong>نسخه‌ها</strong>
          <p>برای وردپرس، تلگرام و کانال‌های دیگر نسخه جدا بساز.</p>
        </a>

        <a className="operator-card" href="/publishing/queue">
          <span></span>
          <strong>صف انتشار</strong>
          <p>نسخه آماده را وارد صف کن و دستی اجرا کن.</p>
        </a>

        <a className="operator-card" href="/publishing/attempts">
          <span></span>
          <strong>گزارش انتشار</strong>
          <p>نتیجه اجرای وردپرس، تلگرام و خطاها را بررسی کن.</p>
        </a>
      </section>
    </main>
  );
}
