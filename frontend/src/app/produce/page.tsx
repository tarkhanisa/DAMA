import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function ProducePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="تولید"
        title="چه چیزی می‌خواهی بسازی؟"
        lead="تولید محتوا از اینجا شروع می‌شود. تولید متن فعال است و ابزار ویدیو لوکال هم به‌صورت پایه اضافه شده است."
      >
        <div className="actions">
          <a href="/generate">تولید متن</a>
          <a href="/produce/video">ویدیو لوکال</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="متن و پست" value="فعال" helper="با موتور فعلی تولید محتوا" />
        <StatCard label="ویدیو لوکال" value="پایه" helper="تصویر + پرامپت + تنظیمات" />
        <StatCard label="تصویر" value="بعدی" helper="در فاز تولید رسانه" />
        <StatCard label="پروژه" value="محور اصلی" helper="هر تولید باید به پروژه وصل شود" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/generate">
          <span>۱</span>
          <strong>تولید متن / پست</strong>
          <p>برای سایت، تلگرام، لینکدین یا کمپین، متن مادر بساز.</p>
        </a>

        <a className="operator-card primary-operator-card" href="/produce/video">
          <span>۲</span>
          <strong>تولید ویدیو لوکال</strong>
          <p>تصویر شروع، تصویر پایان اختیاری و پرامپت بده؛ درخواست ویدیو بساز.</p>
        </a>

        <a className="operator-card muted-operator-card" href="/produce">
          <span>۳</span>
          <strong>تولید تصویر</strong>
          <p>در مرحله بعد، تولید تصویر پروژه‌محور از اینجا فعال می‌شود.</p>
        </a>

        <a className="operator-card" href="/projects">
          <span>۴</span>
          <strong>پروژه‌ها</strong>
          <p>پروژه‌هایی که قبلاً تعریف شده‌اند را ببین.</p>
        </a>
      </section>
    </main>
  );
}
