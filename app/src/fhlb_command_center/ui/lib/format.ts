export function fmtNum(v: unknown, digits = 1): string {
  const n = typeof v === "number" ? v : Number(v);
  if (v === null || v === undefined || Number.isNaN(n)) return "-";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtInt(v: unknown): string {
  const n = typeof v === "number" ? v : Number(v);
  if (v === null || v === undefined || Number.isNaN(n)) return "-";
  return Math.round(n).toLocaleString("en-US");
}

export function fmtUsdBn(v: unknown): string {
  return `$${fmtNum(v, 1)}B`;
}

export function fmtUsdMm(v: unknown): string {
  return `$${fmtNum(v, 1)}M`;
}

export function fmtPct(v: unknown, digits = 1): string {
  return `${fmtNum(v, digits)}%`;
}

export function titleCase(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];
