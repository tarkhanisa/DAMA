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

export function labelBoolean(value: boolean | undefined | null): string {
  return value ? "بله" : "خیر";
}

export function shortId(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  if (text.length <= 10) {
    return text;
  }

  return `${text.slice(0, 6)}${text.slice(-4)}`;
}

export function formatPersianDate(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  const date = new Date(text);

  if (Number.isNaN(date.getTime())) {
    return text;
  }

  return date.toLocaleString("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}

export function friendlyErrorMessage(value: string | undefined | null): string {
  const text = String(value ?? "").trim();

  if (!text) {
    return "";
  }

  const lowered = text.toLowerCase();

  if (lowered.includes("failed to fetch") || lowered.includes("fetch")) {
    return "ارتباط با سرور برقرار نشد.";
  }

  if (text.includes("HTTP 404")) {
    return "مسیر موردنظر پیدا نشد.";
  }

  if (text.includes("HTTP 500")) {
    return "خطای داخلی سرور رخ داد.";
  }

  if (lowered.includes("timeout") || lowered.includes("timed out")) {
    return "زمان اتصال تمام شد. اتصال اینترنت یا VPN را بررسی کن.";
  }

  if (lowered.includes("telegram")) {
    return "اتصال یا ارسال تلگرام نیازمند بررسی است.";
  }

  if (lowered.includes("wordpress")) {
    return "اتصال یا ساخت پیش‌نویس وردپرس نیازمند بررسی است.";
  }

  return text;
}

export function attemptResultSummary(status: string | undefined | null): string {
  const key = String(status ?? "").trim();

  if (key === "draft_created") {
    return "پیش‌نویس وردپرس با موفقیت ساخته شده است.";
  }

  if (key === "test_sent") {
    return "پیام تست تلگرام با موفقیت ارسال شده است.";
  }

  if (key === "dry_run") {
    return "اجرای آزمایشی انجام شده و چیزی واقعاً منتشر نشده است.";
  }

  if (key === "failed") {
    return "این اجرا ناموفق بوده و باید جزئیات بررسی شود.";
  }

  if (key === "blocked") {
    return "این اجرا به‌دلیل ناقص‌بودن تنظیمات یا شرط ایمنی متوقف شده است.";
  }

  return "نتیجه این اجرا در جزئیات ثبت شده است.";
}
