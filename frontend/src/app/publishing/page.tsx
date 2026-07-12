import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function PublishingHomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار"
        title="مرکز ساده انتشار"
        lead="اینجا فقط مسیرهای اصلی انتشار را می‌بینی. تنظیمات فنی و صفحات کم‌استفاده به بخش پیشرفته منتقل شده‌اند."
      >
        <div className="actions">
          <a href="/publishing/queue">صف انتشار</a>
          <a href="/publishing/attempts">گزارش‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="صف انتشار" value="اصلی" helper="مسیر امن اجرا" />
        <StatCard label="وردپرس" value="Draft" helper="بدون Publish مستقیم" />
        <StatCard label="تلگرام" value="Test" helper="ارسال تست کنترل‌شده" />
        <StatCard label="گزارش‌ها" value="ثبت کامل" helper="هر اجرا یک attempt" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/publishing/queue">
          <span></span>
          <strong>صف انتشار</strong>
          <p>نسخه آماده را وارد صف کن و دستی اجرا کن.</p>
        </a>

        <a className="operator-card" href="/publishing/variants">
          <span></span>
          <strong>نسخه‌ها</strong>
          <p>نسخه‌های مخصوص وردپرس و تلگرام را بساز و بازبینی کن.</p>
        </a>

        <a className="operator-card" href="/publishing/attempts">
          <span></span>
          <strong>گزارش انتشار</strong>
          <p>نتیجه اجرای وردپرس، تلگرام و خطاها را بررسی کن.</p>
        </a>

        <a className="operator-card" href="/settings">
          <span></span>
          <strong>تنظیمات اتصال</strong>
          <p>وضعیت وردپرس و تلگرام را از یک جای ساده ببین.</p>
        </a>
      </section>
    </main>
  );
}
