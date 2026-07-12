const queueStatusLabels: Record<string, string> = {
  queued: "در صف",
  running: "در حال اجرا",
  dry_run_completed: "اجرای آزمایشی انجام شد",
  sent: "انجام شد",
  failed: "خطا",
  blocked: "مسدود شده",
  cancelled: "لغو شده"
};

const attemptStatusLabels: Record<string, string> = {
  draft_created: "پیش‌نویس ساخته شد",
  test_sent: "پیام تست ارسال شد",
  dry_run: "اجرای آزمایشی انجام شد",
  failed: "خطا",
  blocked: "مسدود شده",
  pending: "در انتظار",
  ready: "آماده",
  unknown: "نامشخص"
};

const variantStatusLabels: Record<string, string> = {
  draft: "پیش‌نویس",
  ready_for_review: "آماده بازبینی",
  approved: "تأیید شده",
  ready_for_publish: "آماده انتشار",
  scheduled: "زمان‌بندی شده",
  published: "منتشر شده",
  rejected: "رد شده",
  failed: "خطا"
};

const connectorLabels: Record<string, string> = {
  wordpress: "وردپرس",
  telegram: "تلگرام",
  instagram: "اینستاگرام",
  linkedin: "لینکدین",
  whatsapp: "واتساپ",
  bale: "بله",
  eitaa: "ایتا",
  manual: "دستی"
};

const modeLabels: Record<string, string> = {
  dry_run: "اجرای آزمایشی امن",
  wordpress: "ساخت پیش‌نویس وردپرس",
  telegram: "ارسال تست تلگرام"
};

export function labelQueueStatus(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return queueStatusLabels[key] ?? "نامشخص";
}

export function labelAttemptStatus(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return attemptStatusLabels[key] ?? "نامشخص";
}

export function labelVariantStatus(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return variantStatusLabels[key] ?? "نامشخص";
}

export function labelConnector(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return connectorLabels[key] ?? "کانال";
}

export function labelMode(value: string | undefined | null): string {
  const key = String(value ?? "").trim();
  return modeLabels[key] ?? "اجرای آزمایشی امن";
}

export function labelReady(value: boolean | undefined | null): string {
  return value ? "آماده" : "نیازمند بررسی";
}

export function friendlyErrorMessage(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  if (text.includes("Failed to fetch") || text.includes("fetch")) {
    return "ارتباط با سرور برقرار نشد.";
  }

  if (text.includes("HTTP 404")) {
    return "مسیر موردنظر پیدا نشد.";
  }

  if (text.includes("HTTP 500")) {
    return "خطای داخلی سرور رخ داد.";
  }

  if (text.toLowerCase().includes("timeout")) {
    return "زمان اتصال تمام شد. اتصال اینترنت یا VPN را بررسی کن.";
  }

  return text;
}
