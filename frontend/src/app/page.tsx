import { PageHeader } from "../components/page-header";
import { StatCard } from "../components/stat-card";

export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="DAMA"
        title="داشبورد ساده عملیات محتوا"
        lead="از اینجا مسیر روزمره را شروع کن: تولید محتوا، آماده‌سازی انتشار، و بررسی نتیجه‌ها."
      >
        <div className="actions">
          <a href="/generate">تولید محتوا</a>
          <a href="/publishing">انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="مسیر اصلی" value="تولید  انتشار" helper="برای کار روزمره" />
        <StatCard label="وردپرس" value="Draft" helper="ساخت پیش‌نویس واقعی" />
        <StatCard label="تلگرام" value="Test Send" helper="ارسال تست واقعی" />
        <StatCard label="صف انتشار" value="دستی" helper="ایمن و قابل کنترل" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/generate">
          <span></span>
          <strong>تولید محتوا</strong>
          <p>متن مادر را بساز یا محتوای آماده را وارد کن.</p>
        </a>

        <a className="operator-card" href="/publishing/variants">
          <span></span>
          <strong>نسخه‌سازی</strong>
          <p>برای وردپرس، تلگرام و کانال‌های دیگر نسخه جدا بساز.</p>
        </a>

        <a className="operator-card" href="/publishing/queue">
          <span></span>
          <strong>صف انتشار</strong>
          <p>نسخه‌های تأییدشده را وارد صف کن و دستی اجرا کن.</p>
        </a>

        <a className="operator-card" href="/publishing/attempts">
          <span></span>
          <strong>گزارش‌ها</strong>
          <p>نتیجه Draft وردپرس، پیام تلگرام و خطاها را ببین.</p>
        </a>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">اصل کار</p>
          <h2>مسیر پیشنهادی روزانه</h2>
        </div>

        <ol className="simple-steps">
          <li>اول محتوا را تولید کن.</li>
          <li>بعد برای کانال‌ها نسخه بساز.</li>
          <li>نسخه را بازبینی و تأیید کن.</li>
          <li>آن را به صف انتشار اضافه کن.</li>
          <li>اول Dry-run بزن؛ بعد اجرای واقعی.</li>
        </ol>
      </section>
    </main>
  );
}
