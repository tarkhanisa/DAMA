export function formatNumber(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === "") {
    return "0";
  }

  const numberValue = typeof value === "number" ? value : Number(value);

  if (Number.isNaN(numberValue)) {
    return String(value);
  }

  return new Intl.NumberFormat("en").format(numberValue);
}

export function formatBytes(value: number | undefined | null): string {
  if (!value) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size = size / 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

export function fallback(value: string | undefined | null, empty = "—"): string {
  const normalized = String(value ?? "").trim();
  return normalized || empty;
}
