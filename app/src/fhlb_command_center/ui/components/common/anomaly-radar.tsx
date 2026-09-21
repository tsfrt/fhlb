import { useEffect, useRef, useState } from "react";
import {
  Radar,
  Loader2,
  RotateCcw,
  Link2,
  ShieldCheck,
  ChevronDown,
  AlertTriangle,
  Telescope,
} from "lucide-react";
import type { AgentReportBlock, CitationSource } from "@/lib/genie-agent";
import { PERSONA_MAP, type PersonaId } from "@/lib/personas";
import { cn } from "@/lib/utils";
import { askGenie } from "@/lib/genie-bus";
import { Badge } from "@/components/ui/badge";
import { Markdown } from "./markdown";
import { GenieResult } from "./genie-result";

type AnomalyData = {
  persona: string;
  exists: boolean;
  stale: boolean;
  scan_date?: string | null;
  generated_at?: string | null;
  generated_by?: string | null;
  summary?: string | null;
  high: number;
  medium: number;
  low: number;
  content: string;
  blocks?: AgentReportBlock[] | null;
  sources?: CitationSource[] | null;
  steps?: number | null;
  engine?: string;
};

// Persist the last result per persona for the session so navigating between
// cockpits doesn't refetch. The server enforces the once-per-day cadence.
const CACHE = new Map<PersonaId, AnomalyData>();
// Guards against auto-triggering a run more than once per persona per session
// (e.g. React strict-mode double effects, or quick navigation).
const ATTEMPTED = new Set<PersonaId>();

export function AnomalyRadar({ persona }: { persona: PersonaId }) {
  const [data, setData] = useState<AnomalyData | null>(CACHE.get(persona) ?? null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const mounted = useRef(true);

  const runScan = async () => {
    ATTEMPTED.add(persona);
    setRunning(true);
    setError("");
    try {
      const res = await fetch(`/api/ai/anomalies/${persona}`, { method: "POST" });
      if (!res.ok) {
        let msg = `Scan failed (${res.status})`;
        try {
          const j = await res.json();
          msg = j.detail || j.message || msg;
        } catch {
          /* ignore */
        }
        throw new Error(msg);
      }
      const json = (await res.json()) as AnomalyData;
      CACHE.set(persona, json);
      if (mounted.current) setData(json);
    } catch (e) {
      if (mounted.current) setError((e as Error).message);
    } finally {
      if (mounted.current) setRunning(false);
    }
  };

  useEffect(() => {
    mounted.current = true;
    const cached = CACHE.get(persona);
    if (cached) {
      setData(cached);
      if (cached.stale && !ATTEMPTED.has(persona)) void runScan();
      return () => {
        mounted.current = false;
      };
    }
    // Fetch the cached scan; auto-run only if there's none for today.
    (async () => {
      try {
        const res = await fetch(`/api/ai/anomalies/${persona}`);
        const json = (await res.json()) as AnomalyData;
        CACHE.set(persona, json);
        if (!mounted.current) return;
        setData(json);
        if ((!json.exists || json.stale) && !ATTEMPTED.has(persona)) void runScan();
      } catch {
        if (mounted.current && !ATTEMPTED.has(persona)) void runScan();
      }
    })();
    return () => {
      mounted.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persona]);

  const has = !!data?.exists && !!data?.content;
  const blocks = (data?.blocks as AgentReportBlock[] | null | undefined) ?? null;
  const sources = (data?.sources as CitationSource[] | null | undefined) ?? [];
  const short = PERSONA_MAP[persona]?.short ?? "";

  return (
    <div className="glass-persona relative overflow-hidden rounded-xl">
      <div className="exec-grid absolute inset-0 opacity-40" />
      <div className="relative">
        {/* Header — always visible; acts as the collapse toggle */}
        <div className="flex items-center gap-3 px-5 py-3.5">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            disabled={!has}
            className="flex min-w-0 flex-1 items-center gap-2.5 text-left disabled:cursor-default"
          >
            <span className="persona-text grid size-6 shrink-0 place-items-center">
              <Radar className={cn("size-4", running && "animate-spin [animation-duration:3s]")} />
            </span>
            <span className="shrink-0 text-sm font-semibold">AI Anomaly Radar</span>
            <Badge
              variant="outline"
              className="hidden shrink-0 gap-1 border-emerald-500/40 text-emerald-300 sm:inline-flex"
            >
              <ShieldCheck className="size-3" /> Genie deep research
            </Badge>

            {/* Collapsed summary line */}
            <span className="ml-1 flex min-w-0 flex-1 items-center gap-2">
              {has && <SeverityChips high={data!.high} medium={data!.medium} low={data!.low} />}
              <span className="truncate text-xs text-muted-foreground">
                {running && !has
                  ? `Scanning ${short} data for anomalies…`
                  : error && !has
                    ? error
                    : has
                      ? data!.summary || "View findings"
                      : "No scan yet"}
              </span>
            </span>
          </button>

          <div className="flex shrink-0 items-center gap-1.5">
            {running && <Loader2 className="persona-text size-3.5 animate-spin" />}
            <button
              type="button"
              onClick={() => void runScan()}
              disabled={running}
              title="Re-scan now"
              className="grid size-7 place-items-center rounded-md text-muted-foreground transition hover:text-foreground disabled:opacity-40"
            >
              <RotateCcw className="size-3.5" />
            </button>
            {has && (
              <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="grid size-7 place-items-center rounded-md text-muted-foreground transition hover:text-foreground"
              >
                <ChevronDown className={cn("size-4 transition-transform", open && "rotate-180")} />
              </button>
            )}
          </div>
        </div>

        {/* Expanded findings */}
        {open && has && (
          <div className="animate-fade-up space-y-3 border-t border-border/50 px-5 pb-5 pt-4">
            {blocks && blocks.length > 0 ? (
              blocks.map((b, i) =>
                b.kind === "text" ? (
                  <Findings key={i} text={b.text} sources={sources} persona={persona} />
                ) : (
                  <GenieResult key={i} columns={b.columns} rows={b.rows} sql={b.sql} />
                ),
              )
            ) : (
              <Findings text={data!.content} sources={sources} persona={persona} />
            )}

            {sources.length > 0 && (
              <div className="border-t border-border/50 pt-3">
                <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  <Link2 className="persona-text size-3" /> Evidence
                </div>
                <ol className="space-y-1">
                  {sources.map((s) => (
                    <li key={s.n} className="flex gap-2 text-xs leading-relaxed">
                      <span className="persona-text tnum shrink-0 font-semibold">[{s.n}]</span>
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        title={s.sql ?? "Open query in Genie"}
                        className="text-foreground/85 underline-offset-2 hover:text-foreground hover:underline"
                      >
                        {s.title}
                      </a>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 pt-1 text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1">
                <ShieldCheck className="size-3 text-emerald-400" /> Genie deep research · Unity Catalog governed
              </span>
              {typeof data!.steps === "number" && <span>{data!.steps} research steps</span>}
              {data!.generated_at && <span>Scanned {data!.generated_at}</span>}
              {data!.stale && <span className="text-amber-400">refreshing…</span>}
            </div>
          </div>
        )}

        {/* Error state when there's nothing to show */}
        {error && !has && !running && (
          <div className="flex items-start gap-2 border-t border-border/50 px-5 pb-4 pt-3 text-xs text-destructive">
            <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}

type Finding = { raw: string; citations: number[] };

// Citation markers arrive as ``[\[n\]](url)`` (Markdown-escaped brackets).
const CITE_RE = /\[\\\[(\d+)\\\]\]\([^)]*\)/g;
const BULLET_RE = /^\s*(?:[-*]|\d+[.)])\s+/;

/** Split the findings markdown into individual findings, capturing the citation
 * numbers each one references so we can attach the related source query. */
function splitFindings(text: string): Finding[] {
  const items: Finding[] = [];
  let cur: string[] | null = null;
  const flush = () => {
    if (!cur) return;
    const raw = cur.join(" ").replace(/\s+/g, " ").trim();
    if (raw) {
      const cites = [...raw.matchAll(CITE_RE)].map((m) => Number(m[1]));
      items.push({ raw, citations: [...new Set(cites)] });
    }
    cur = null;
  };
  for (const line of (text || "").split("\n")) {
    if (BULLET_RE.test(line)) {
      flush();
      cur = [line.replace(BULLET_RE, "")];
    } else if (line.trim()) {
      if (cur) cur.push(line.trim());
      else cur = [line.trim()];
    } else {
      flush();
    }
  }
  flush();
  return items;
}

function cleanFinding(raw: string): string {
  return raw
    .replace(CITE_RE, "")
    .replace(/\*\*/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function investigatePrompt(personaLabel: string, finding: Finding, sources: CitationSource[]): string {
  const sqls = finding.citations
    .map((n) => sources.find((s) => s.n === n)?.sql)
    .filter((s): s is string => !!s);
  const sqlBlock = sqls.length
    ? `\n\nThe query that surfaced this finding:\n\`\`\`sql\n${sqls[0].trim()}\n\`\`\``
    : "";
  return (
    `Investigate this anomaly for ${personaLabel} at FHLB Des Moines. Confirm whether it is a ` +
    `genuine risk or a data-quality artifact, quantify the impact with current data, identify which ` +
    `members, segments, products, or time periods are driving it, and recommend concrete next steps.` +
    `\n\nFinding: ${cleanFinding(finding.raw)}${sqlBlock}`
  );
}

function Findings({
  text,
  sources,
  persona,
}: {
  text: string;
  sources: CitationSource[];
  persona: PersonaId;
}) {
  const items = splitFindings(text);
  const label = PERSONA_MAP[persona]?.label ?? persona;
  if (items.length === 0) {
    return <Markdown className="text-foreground/90">{text}</Markdown>;
  }
  return (
    <div className="space-y-2">
      {items.map((it, i) => (
        <div
          key={i}
          className="group glass flex items-start justify-between gap-3 rounded-lg px-3 py-2.5"
        >
          <Markdown className="min-w-0 flex-1 text-sm text-foreground/90">{it.raw}</Markdown>
          <button
            type="button"
            onClick={() => askGenie(investigatePrompt(label, it, sources), "agent")}
            title="Investigate with the Genie research agent"
            className="persona-bg-soft persona-ring mt-0.5 inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium text-foreground/85 transition hover:text-foreground"
          >
            <Telescope className="persona-text size-3" />
            Investigate
          </button>
        </div>
      ))}
    </div>
  );
}

function SeverityChips({ high, medium, low }: { high: number; medium: number; low: number }) {
  if (!high && !medium && !low) return null;
  return (
    <span className="flex shrink-0 items-center gap-1">
      {high > 0 && <Chip n={high} className="border-rose-500/40 bg-rose-500/10 text-rose-300" label="High" />}
      {medium > 0 && (
        <Chip n={medium} className="border-amber-500/40 bg-amber-500/10 text-amber-300" label="Med" />
      )}
      {low > 0 && <Chip n={low} className="border-sky-500/40 bg-sky-500/10 text-sky-300" label="Low" />}
    </span>
  );
}

function Chip({ n, label, className }: { n: number; label: string; className: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-medium leading-none tnum",
        className,
      )}
    >
      {n} {label}
    </span>
  );
}
