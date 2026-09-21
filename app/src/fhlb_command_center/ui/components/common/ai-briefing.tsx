import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ShieldCheck,
  Sparkles,
  RefreshCw,
  Loader2,
  Telescope,
  Zap,
  ArrowUpRight,
  Link2,
} from "lucide-react";
import type { GovernedResponse } from "@/lib/api";
import type { AgentReportBlock } from "@/lib/genie-agent";
import type { PersonaId } from "@/lib/personas";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { askGenie } from "@/lib/genie-bus";
import { Markdown } from "./markdown";
import { GenieResult } from "./genie-result";

type Engine = "gateway" | "genie_agent";
const ENGINE_KEY = "fhlb.briefing.engine";

type CitationSource = { n: number; title: string; url: string; sql?: string | null };

type BriefingData = {
  persona: string;
  stale: boolean;
  generated_at?: string | null;
  gateway: GovernedResponse | null;
  genie_agent: GovernedResponse | null;
};

// Session cache + once-per-session run guard, mirroring the Anomaly Radar. The
// server enforces the true once-per-day cadence via scan_date.
const CACHE = new Map<PersonaId, BriefingData>();
const ATTEMPTED = new Set<PersonaId>();

export function AiBriefing({ persona, title = "This morning's briefing" }: { persona: PersonaId; title?: string }) {
  const [data, setData] = useState<BriefingData | null>(CACHE.get(persona) ?? null);
  const [engine, setEngine] = useState<Engine>("gateway");
  const [running, setRunning] = useState(false);
  const mounted = useRef(true);

  useEffect(() => {
    const saved = localStorage.getItem(ENGINE_KEY);
    if (saved === "genie_agent" || saved === "gateway") setEngine(saved);
  }, []);

  const runScan = async () => {
    ATTEMPTED.add(persona);
    setRunning(true);
    try {
      const r = await fetch(`/api/ai/briefings/${persona}`, { method: "POST" });
      if (!r.ok) throw new Error(`Briefing failed (${r.status})`);
      const json = (await r.json()) as BriefingData;
      CACHE.set(persona, json);
      if (mounted.current) setData(json);
    } catch {
      /* leave any stale data in place */
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
    (async () => {
      try {
        const r = await fetch(`/api/ai/briefings/${persona}`);
        const json = (await r.json()) as BriefingData;
        CACHE.set(persona, json);
        if (!mounted.current) return;
        setData(json);
        const missing = !json.gateway || !json.genie_agent;
        if ((missing || json.stale) && !ATTEMPTED.has(persona)) void runScan();
      } catch {
        if (mounted.current && !ATTEMPTED.has(persona)) void runScan();
      }
    })();
    return () => {
      mounted.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persona]);

  const chooseEngine = (e: Engine) => {
    setEngine(e);
    localStorage.setItem(ENGINE_KEY, e);
  };

  const res = engine === "genie_agent" ? data?.genie_agent ?? null : data?.gateway ?? null;
  const blocks = (res?.blocks as AgentReportBlock[] | null | undefined) ?? null;
  const sources = (res?.sources as CitationSource[] | null | undefined) ?? [];
  const isGenie = (res?.engine ?? engine) === "genie_agent";

  return (
    <div className="glass-persona relative overflow-hidden rounded-xl p-5">
      <div className="exec-grid absolute inset-0 opacity-40" />
      <div className="relative">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="persona-text size-4" />
            <span className="text-sm font-semibold">{title}</span>
            <Badge variant="outline" className="gap-1 border-emerald-500/40 text-emerald-300">
              <ShieldCheck className="size-3" /> Governed AI
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <EngineToggle engine={engine} onChange={chooseEngine} />
            <Button size="icon" variant="ghost" className="size-7" onClick={() => void runScan()} disabled={running}>
              {running ? <Loader2 className="size-3.5 animate-spin" /> : <RefreshCw className="size-3.5" />}
            </Button>
          </div>
        </div>

        {!res && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="persona-text size-4 animate-spin" />
            {running
              ? engine === "genie_agent"
                ? "Genie is researching the lakehouse…"
                : "Routing through the AI Gateway…"
              : "Loading briefing…"}
          </p>
        )}

        {res && (
          <div className="animate-fade-up">
            {blocks && blocks.length > 0 ? (
              <div className="space-y-3">
                {blocks.map((b, i) =>
                  b.kind === "text" ? (
                    <Markdown key={i} className="text-foreground/90">
                      {b.text}
                    </Markdown>
                  ) : (
                    <GenieResult key={i} columns={b.columns} rows={b.rows} sql={b.sql} />
                  ),
                )}
              </div>
            ) : (
              <Markdown className="text-foreground/90">{res.content}</Markdown>
            )}

            {sources.length > 0 && (
              <div className="mt-4 border-t border-border/50 pt-3">
                <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  <Link2 className="persona-text size-3" /> Sources
                </div>
                <ol className="space-y-1">
                  {sources.map((s) => (
                    <li key={s.n} className="flex gap-2 text-xs leading-relaxed">
                      <span className="persona-text shrink-0 font-semibold tnum">[{s.n}]</span>
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

            {res.follow_ups && res.follow_ups.length > 0 && (
              <div className="mt-4 border-t border-border/50 pt-3">
                <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  <Sparkles className="persona-text size-3" /> Suggested follow-ups
                </div>
                <div className="flex flex-wrap gap-2">
                  {res.follow_ups.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => askGenie(q)}
                      title="Ask Genie"
                      className="persona-bg-soft persona-ring group inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-left text-xs text-foreground/85 transition hover:text-foreground"
                    >
                      {q}
                      <ArrowUpRight className="persona-text size-3 opacity-60 transition group-hover:opacity-100" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
              <span>
                engine:{" "}
                <span className="persona-text font-medium">
                  {isGenie ? "Genie deep research" : "AI Gateway (Claude)"}
                </span>
              </span>
              <span>
                endpoint: <span className="persona-text font-medium">{res.endpoint}</span>
              </span>
              <span>
                guardrails: <span className="font-medium text-emerald-300">{res.guardrail_verdict}</span>
              </span>
              {isGenie && res.steps != null && <span>{res.steps} research steps</span>}
              {res.latency_ms != null && <span>{res.latency_ms.toLocaleString()} ms</span>}
              {data?.generated_at && <span>generated {data.generated_at}</span>}
              {running && <span className="text-amber-400">refreshing…</span>}
              <span className="opacity-70">audited to Lakebase</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EngineToggle({
  engine,
  onChange,
}: {
  engine: Engine;
  onChange: (e: Engine) => void;
}) {
  return (
    <div className="flex items-center gap-0.5 rounded-lg border border-border/60 bg-background/40 p-0.5">
      <EngineBtn active={engine === "gateway"} onClick={() => onChange("gateway")} title="Fast briefing via AI Gateway (Claude)">
        <Zap className="size-3" /> Fast
      </EngineBtn>
      <EngineBtn active={engine === "genie_agent"} onClick={() => onChange("genie_agent")} title="Deep research via Genie Agent mode">
        <Telescope className="size-3" /> Deep
      </EngineBtn>
    </div>
  );
}

function EngineBtn({
  active,
  onClick,
  title,
  children,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={cn(
        "flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition",
        active ? "persona-bg-soft persona-text" : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}
