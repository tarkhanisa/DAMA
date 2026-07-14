import { PageHeader } from "../../../components/page-header";
import { SafeExitAction } from "../../../components/safe-exit-action";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function SafeExitPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="خروج امن"
        title="بستن امن داشبورد DAMA"
        lead="آخرین صفحه ذخیره می‌شود، از داده‌های runtime پشتیبان گرفته می‌شود و سرورهای محلی داشبورد بسته می‌شوند."
      >
        <div className="actions">
          <a href="/">بازگشت به داشبورد</a>
          <a href="/other">سایر</a>
        </div>
      </PageHeader>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">عملیات</p>
            <h2>خروج امن</h2>
          </div>

          <p className="muted-note">
            این کار Ollama را نمی‌بندد. فقط backend و frontend مربوط به DAMA را متوقف می‌کند.
            داده‌های کاری که داخل فایل‌های runtime ذخیره شده‌اند از بین نمی‌روند.
          </p>

          <SafeExitAction apiBaseUrl={API_BASE_URL} />
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">دفعه بعد</p>
            <h2>شروع از آخرین صفحه</h2>
          </div>

          <ol className="simple-steps">
            <li>برای شروع بعدی از اسکریپت start استفاده کن.</li>
            <li>مرورگر به آخرین صفحه ذخیره‌شده باز می‌شود.</li>
            <li>اگر مرورگر مستقیم صفحه اصلی را باز کرد، کارت «ادامه کار قبلی» را می‌بینی.</li>
          </ol>

          <pre className="json-block">cd I:\DAMA
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\dama-start.ps1 -CleanPorts</pre>
        </section>
      </section>
    </main>
  );
}
