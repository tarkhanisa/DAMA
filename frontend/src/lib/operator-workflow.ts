export type OperatorSignal = {
  wordpressReady: boolean;
  telegramReady: boolean;
  variantCount: number;
  readyVariantCount: number;
  queueCount: number;
  queuedCount: number;
  failedQueueCount: number;
  attemptCount: number;
  failedAttemptCount: number;
  latestAttemptStatus: string;
};

export type OperatorChecklistItem = {
  step: number;
  title: string;
  description: string;
  href: string;
  actionLabel: string;
  state: "done" | "active" | "pending" | "warning";
};

export function buildOperatorChecklist(signal: OperatorSignal): OperatorChecklistItem[] {
  const connectorReady = signal.wordpressReady || signal.telegramReady;

  return [
    {
      step: 1,
      title: "اتصال‌ها را آماده کن",
      description: connectorReady
        ? "حداقل یکی از اتصال‌های وردپرس یا تلگرام آماده است."
        : "قبل از انتشار، وضعیت وردپرس یا تلگرام را بررسی کن.",
      href: "/settings",
      actionLabel: "بررسی تنظیمات",
      state: connectorReady ? "done" : "active"
    },
    {
      step: 2,
      title: "محتوا تولید کن",
      description: signal.variantCount > 0
        ? "نسخه‌هایی برای انتشار ساخته شده‌اند."
        : "یک متن مادر بساز یا محتوای آماده را وارد کن.",
      href: "/generate",
      actionLabel: "تولید محتوا",
      state: signal.variantCount > 0 ? "done" : connectorReady ? "active" : "pending"
    },
    {
      step: 3,
      title: "نسخه کانالی را آماده کن",
      description: signal.readyVariantCount > 0
        ? "حداقل یک نسخه آماده انتشار وجود دارد."
        : "برای وردپرس یا تلگرام نسخه کانالی بساز و تأیید کن.",
      href: "/publishing/variants",
      actionLabel: "رفتن به نسخه‌ها",
      state: signal.readyVariantCount > 0 ? "done" : signal.variantCount > 0 ? "active" : "pending"
    },
    {
      step: 4,
      title: "به صف انتشار اضافه کن",
      description: signal.queueCount > 0
        ? "آیتم‌هایی در صف انتشار ثبت شده‌اند."
        : "نسخه تأییدشده را وارد صف انتشار کن.",
      href: "/publishing/queue",
      actionLabel: "مدیریت صف",
      state: signal.queueCount > 0 ? "done" : signal.readyVariantCount > 0 ? "active" : "pending"
    },
    {
      step: 5,
      title: "اجرا و گزارش را بررسی کن",
      description: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "چند مورد نیازمند بررسی وجود دارد."
        : signal.attemptCount > 0
          ? "گزارش‌های اجرا ثبت شده‌اند."
          : "اول اجرای آزمایشی امن را انجام بده و نتیجه را ببین.",
      href: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "/publishing/attempts"
        : "/publishing/queue",
      actionLabel: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "بررسی خطاها"
        : signal.attemptCount > 0
          ? "دیدن گزارش‌ها"
          : "اجرای آزمایشی",
      state: signal.failedAttemptCount > 0 || signal.failedQueueCount > 0
        ? "warning"
        : signal.attemptCount > 0
          ? "done"
          : signal.queueCount > 0
            ? "active"
            : "pending"
    }
  ];
}

export function getOperatorNextAction(signal: OperatorSignal): OperatorChecklistItem {
  const checklist = buildOperatorChecklist(signal);

  return (
    checklist.find((item) => item.state === "warning") ??
    checklist.find((item) => item.state === "active") ??
    checklist[checklist.length - 1]
  );
}
