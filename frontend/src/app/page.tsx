import { PageHeader } from "../components/page-header";

export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="DAMA"
        title="چه کاری میخواهی انجام بدهی"
        lead="برای سادهتر شدن کار پنل به سه بخش اصلی تقسیم شده است: تولید انتشار و سایر."
      />

      <section className="three-door-console" aria-label="درهای اصلی پنل">
        <a className="door-card door-primary" href="/produce">
          <span></span>
          <strong>تولید</strong>
          <p>متن ایده پست تصویر یا ویدیو را برای یک پروژه آماده کن.</p>
          <em>شروع تولید محتوا</em>
        </a>

        <a className="door-card door-primary" href="/publishing">
          <span></span>
          <strong>انتشار</strong>
          <p>پروژه را انتخاب کن متن و رسانه را وارد کن کانالها را انتخاب کن و برای انتشار آماده شو.</p>
          <em>شروع انتشار</em>
        </a>

        <a className="door-card" href="/other">
          <span></span>
          <strong>سایر</strong>
          <p>گزارشها تنظیمات تاریخچه پشتیبان پاکسازی و ابزارهای فنی.</p>
          <em>رفتن به ابزارها</em>
        </a>
      </section>

      <section className="panel quiet-panel">
        <div className="panel-heading">
          <p className="eyebrow">مسیر پیشنهادی</p>
          <h2>برای کار روزمره</h2>
        </div>

        <ol className="simple-steps">
          <li>اگر میخواهی چیزی بسازی از تولید شروع کن.</li>
          <li>اگر محتوایت آماده است و میخواهی منتشر کنی از انتشار شروع کن.</li>
          <li>اگر میخواهی گزارشها تنظیمات یا پاکسازی را ببینی برو به سایر.</li>
        </ol>
      </section>
    </main>
  );
}
