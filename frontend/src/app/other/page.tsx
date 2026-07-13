import { PageHeader } from "../../components/page-header";

export const dynamic = "force-dynamic";

const groups = [
  {
    title: "گزارش و تاریخچه",
    items: [
      {
        href: "/publishing/attempts",
        title: "گزارش انتشار",
        description: "نتیجه اجرای وردپرس، تلگرام، dry-run و خطاها."
      },
      {
        href: "/publishing/campaigns",
        title: "کمپین‌های قبلی",
        description: "کمپین‌هایی که برای انتشار ساخته شده‌اند."
      },
      {
        href: "/publishing/queue",
        title: "صف انتشار",
        description: "آیتم‌هایی که برای اجرا آماده شده‌اند."
      }
    ]
  },
  {
    title: "تنظیمات و نگهداری",
    items: [
      {
        href: "/settings",
        title: "تنظیمات اتصال",
        description: "وضعیت وردپرس و تلگرام."
      },
      {
        href: "/advanced/cleanup",
        title: "پاک‌سازی داده‌های تستی",
        description: "حذف امن داده‌های smoke/test با backup."
      },
      {
        href: "/maintenance",
        title: "نگهداری",
        description: "ابزارهای نگهداری سیستم."
      }
    ]
  },
  {
    title: "ابزارهای فنی",
    items: [
      {
        href: "/advanced",
        title: "پیشرفته",
        description: "همه ابزارهای کم‌استفاده و فنی."
      },
      {
        href: "/runtime",
        title: "سلامت سیستم",
        description: "بررسی وضعیت backend و سرویس‌ها."
      },
      {
        href: "/projects",
        title: "پروژه‌ها",
        description: "فهرست و مدیریت پروژه‌ها."
      },
      {
        href: "/content-assets",
        title: "محتواها",
        description: "دارایی‌های محتوایی ثبت‌شده."
      }
    ]
  }
];

export default function OtherPage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="سایر"
        title="گزارش‌ها، تنظیمات و ابزارهای فنی"
        lead="هر چیزی که کار روزمره تولید و انتشار نیست، اینجا قرار می‌گیرد تا داشبورد اصلی شلوغ نشود."
      >
        <div className="actions">
          <a href="/">داشبورد</a>
          <a href="/advanced">پیشرفته</a>
        </div>
      </PageHeader>

      <section className="other-groups">
        {groups.map((group) => (
          <section className="panel" key={group.title}>
            <div className="panel-heading">
              <p className="eyebrow">سایر</p>
              <h2>{group.title}</h2>
            </div>

            <div className="operator-grid">
              {group.items.map((item) => (
                <a className="operator-card" href={item.href} key={item.href}>
                  <span>•</span>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </a>
              ))}
            </div>
          </section>
        ))}
      </section>
    </main>
  );
}
