import { PageHeader } from "../../components/page-header";

export const dynamic = "force-dynamic";

const advancedLinks = [
  {
    href: "/runtime",
    title: "سلامت سیستم",
    description: "وضعیت backend، مدل‌ها و سرویس‌ها."
  },
  {
    href: "/operations",
    title: "عملیات",
    description: "ابزارهای عملیاتی و تست‌های داخلی."
  },
  {
    href: "/exports",
    title: "خروجی‌ها",
    description: "مدیریت خروجی‌های ساخته‌شده."
  },
  {
    href: "/maintenance",
    title: "نگهداری",
    description: "کارهای فنی و پاک‌سازی."
  },
  {
    href: "/workflows",
    title: "جریان کار",
    description: "مدیریت workflowهای داخلی."
  },
  {
    href: "/search",
    title: "جستجو",
    description: "جستجو در داده‌ها و محتواها."
  }
];

export default function AdvancedPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="پیشرفته"
        title="ابزارهای فنی و کم‌استفاده"
        lead="این بخش برای وقتی است که بخواهی وضعیت سیستم، ابزارهای فنی یا خروجی‌ها را بررسی کنی."
      >
        <div className="actions">
          <a href="/">داشبورد</a>
          <a href="/settings">تنظیمات</a>
        </div>
      </PageHeader>

      <section className="operator-grid">
        {advancedLinks.map((item) => (
          <a className="operator-card" href={item.href} key={item.href}>
            <span></span>
            <strong>{item.title}</strong>
            <p>{item.description}</p>
          </a>
        ))}
      </section>
    </main>
  );
}
