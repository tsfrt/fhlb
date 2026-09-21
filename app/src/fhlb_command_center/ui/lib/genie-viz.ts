export type Row = Record<string, unknown>;

export type ChartPlan =
  | { kind: "kpi"; column: string }
  | { kind: "chart"; type: "bar" | "line" | "area" | "donut"; x: string; series: string[] }
  | { kind: "table" };

const ID_RE = /(^id$|_id$|_code$|zip|postal|fips|phone|year_month)/i;
const DATE_RE = /(date|month|quarter|year|day|period|week|time|as_of|vintage|fy|qtr)/i;
const SHARE_RE = /(share|pct|percent|mix|proportion|ratio)/i;

export function asNumber(v: unknown): number | null {
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v === "string") {
    const cleaned = v.replace(/[$,%\s]/g, "");
    if (cleaned === "" || cleaned === "-") return null;
    const n = Number(cleaned);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function isNumericColumn(col: string, rows: Row[]): boolean {
  let num = 0;
  let seen = 0;
  for (const r of rows) {
    const v = r[col];
    if (v === null || v === undefined || v === "") continue;
    seen++;
    if (asNumber(v) !== null) num++;
  }
  return seen > 0 && num / seen >= 0.8;
}

function isDateLike(col: string, rows: Row[]): boolean {
  if (DATE_RE.test(col)) return true;
  // sniff a few values for ISO-ish dates
  let hits = 0;
  let seen = 0;
  for (const r of rows.slice(0, 8)) {
    const v = r[col];
    if (typeof v !== "string") continue;
    seen++;
    if (/^\d{4}-\d{2}(-\d{2})?/.test(v) || !Number.isNaN(Date.parse(v))) hits++;
  }
  return seen > 0 && hits / seen >= 0.6;
}

/** Decide how to render a Genie/SQL result: KPI, a chart, or a plain table. */
export function analyzeResult(columns: string[], rows: Row[]): ChartPlan {
  if (!columns.length || !rows.length) return { kind: "table" };

  const numeric = columns.filter((c) => isNumericColumn(c, rows));
  const measures = numeric.filter((c) => !ID_RE.test(c) && !/^year$|^month$|^quarter$|^day$/i.test(c));
  const dimensions = columns.filter((c) => !measures.includes(c));

  // Single headline number.
  if (rows.length === 1 && measures.length === 1) {
    return { kind: "kpi", column: measures[0] };
  }

  if (measures.length >= 1 && dimensions.length >= 1 && rows.length >= 2 && rows.length <= 60) {
    const dateDim = dimensions.find((c) => isDateLike(c, rows));
    const x = dateDim ?? dimensions.find((c) => !measures.includes(c)) ?? dimensions[0];
    const series = measures.filter((m) => m !== x).slice(0, 4);
    if (series.length === 0) return { kind: "table" };

    if (dateDim) {
      return { kind: "chart", type: series.length === 1 ? "area" : "line", x, series };
    }
    // Categorical: a single share-like measure across few categories -> donut.
    if (series.length === 1 && rows.length <= 8 && SHARE_RE.test(series[0])) {
      return { kind: "chart", type: "donut", x, series };
    }
    return { kind: "chart", type: "bar", x, series };
  }

  return { kind: "table" };
}

/** Normalize rows so chart measures are real numbers and x is a string label. */
export function toChartData(rows: Row[], x: string, series: string[], limit = 60): Row[] {
  return rows.slice(0, limit).map((r) => {
    const out: Row = { [x]: r[x] == null ? "" : String(r[x]) };
    for (const s of series) out[s] = asNumber(r[s]) ?? 0;
    return out;
  });
}

const CURRENCY_RE = /(usd|amount|advance|balance|revenue|subsidy|dollar|par|notional|\$)/i;
const PCT_RE = /(pct|percent|ratio|rate|share|cushion|utilization)/i;

export function measureFormat(col: string): "currency" | "percent" | "number" {
  if (PCT_RE.test(col)) return "percent";
  if (CURRENCY_RE.test(col)) return "currency";
  return "number";
}
