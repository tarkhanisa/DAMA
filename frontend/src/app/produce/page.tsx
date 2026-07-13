import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function ProducePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید"
        title="برای چه پروژه‌ای می‌خواهی محتوا بسازی؟"
        lead="این بخش فعلاً مسیر ساده تولید متن و پست را نگه می‌دارد. تولید تصویر و ویدیو در مرحله‌های بعدی توسعه پیدا می‌کند."
      >
        <div className="actions">
          <a href="/generate">تولید متن</a>
          <a href="/projects">پروژه‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="متن و پست" value="فعال" helper="با موتور فعلی تولید محتوا" />
        <StatCard label="تصویر" value="بعدی" helper="در فاز تولید رسانه" />
        <StatCard label="ویدیو" value="بعدی" helper="در فاز تولید رسانه" />
        <StatCard label="پروژه" value="محور اصلی" helper="هر تولید باید به پروژه وصل شود" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/generate">
          <span>۱</span>
          <strong>تولید متن / پست</strong>
          <p>برای سایت، تلگرام، لینکدین یا کمپین، متن مادر بساز.</p>
        </a>

        <a className="operator-card" href="/projects">
          <span>۲</span>
          <strong>انتخاب یا بررسی پروژه</strong>
          <p>پروژه‌هایی که قبلاً تعریف شده‌اند را ببین.</p>
        </a>

        <a className="operator-card muted-operator-card" href="/produce">
          <span>۳</span>
          <strong>تولید تصویر</strong>
          <p>در مرحله بعد، تولید تصویر پروژه‌محور از اینجا فعال می‌شود.</p>
        </a>

        <a className="operator-card muted-operator-card" href="/produce">
          <span>۴</span>
          <strong>تولید ویدیو</strong>
          <p>در مرحله‌های بعد، تولید ویدیو و آماده‌سازی رسانه اضافه می‌شود.</p>
        </a>
      </section>
    </main>
  );
}
