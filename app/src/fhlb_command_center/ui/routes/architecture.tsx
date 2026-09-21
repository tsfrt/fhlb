import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import {
  Database,
  Sparkles,
  ShieldCheck,
  Server,
  Cpu,
  AppWindow,
  Users,
  ArrowDown,
  Radio,
  Lock,
} from "lucide-react";
import { PERSONAS } from "@/lib/personas";

export const Route = createFileRoute("/architecture")({ component: ArchitectureView });

const BLUE = "0.72 0.14 233";

type Pillar = {
  id: string;
  name: string;
  tech: string;
  api: string;
  accent: string;
  icon: ReactNode;
  points: string[];
  stat: string;
};

const PILLARS: Pillar[] = [
  {
    id: "lakehouse",
    name: "Lakehouse",
    tech: "Unity Catalog + SQL Warehouse",
    api: "Statement Execution API",
    accent: "0.74 0.13 205",
    icon: <Database className="size-5" />,
    points: ["fhlb.des_moines · 38 tables", "Unity Catalog governed", "Serverless SQL warehouse"],
    stat: "$106.6B advances tracked",
  },
  {
    id: "genie",
    name: "Genie",
    tech: "Natural-language analytics",
    api: "Conversation + Agent APIs",
    accent: "0.68 0.19 300",
    icon: <Sparkles className="size-5" />,
    points: ["5 persona Genie spaces", "Standard + Agent (deep research)", "NL → governed SQL"],
    stat: "Ask in plain English",
  },
  {
    id: "gateway",
    name: "AI Gateway",
    tech: "Governed model serving",
    api: "OpenAI-compatible client",
    accent: "0.72 0.14 233",
    icon: <ShieldCheck className="size-5" />,
    points: ["Claude Sonnet, governed", "PII masking · rate limits", "Usage + inference tables"],
    stat: "Guardrails enforced",
  },
  {
    id: "lakebase",
    name: "Lakebase",
    tech: "Managed Postgres (OLTP)",
    api: "psycopg + OAuth",
    accent: "0.8 0.16 85",
    icon: <Server className="size-5" />,
    points: ["Watchlists · exam packs", "AI narrative audit log", "OAuth token refresh"],
    stat: "Millisecond app state",
  },
  {
    id: "serving",
    name: "Model Serving",
    tech: "Classical ML (XGBoost)",
    api: "REST inference API",
    accent: "0.66 0.22 20",
    icon: <Cpu className="size-5" />,
    points: ["Member Early-Warning PD", "Unity Catalog model registry", "Scored on the CRO cockpit"],
    stat: "Risk before the rating moves",
  },
];

const APP_BADGES = ["Service principal (OAuth)", "Auto-scaled compute", "6 persona cockpits"];

function FlowConnector({
  accent = BLUE,
  height = "h-14",
  packets = 2,
}: {
  accent?: string;
  height?: string;
  packets?: number;
}) {
  return (
    <div
      className={`arch-line mx-auto ${height}`}
      style={{ ["--persona" as string]: `oklch(${accent})` }}
    >
      {Array.from({ length: packets }).map((_, i) => (
        <span
          key={i}
          className="arch-packet"
          style={{ animationDelay: `${i * 1.2}s` }}
        />
      ))}
    </div>
  );
}

function PillarCard({ p, index }: { p: Pillar; index: number }) {
  return (
    <div
      className="animate-fade-up glass-persona flex flex-col gap-3 rounded-2xl p-4"
      style={{
        ["--persona" as string]: `oklch(${p.accent})`,
        animationDelay: `${300 + index * 90}ms`,
      }}
    >
      <div className="flex items-center gap-3">
        <div className="persona-bg-soft persona-text arch-float grid size-11 place-items-center rounded-xl">
          {p.icon}
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold">{p.name}</div>
          <div className="truncate text-[11px] text-muted-foreground">{p.tech}</div>
        </div>
      </div>
      <ul className="space-y-1.5">
        {p.points.map((pt) => (
          <li key={pt} className="flex items-start gap-2 text-xs text-foreground/85">
            <span className="persona-text mt-1 size-1.5 shrink-0 rounded-full bg-[var(--persona)]" />
            {pt}
          </li>
        ))}
      </ul>
      <div className="persona-text mt-auto text-xs font-semibold">{p.stat}</div>
    </div>
  );
}

function ApiLabel({ children, accent }: { children: ReactNode; accent: string }) {
  return (
    <div
      className="mx-auto w-fit rounded-full border border-border/60 bg-background/50 px-2.5 py-1 text-[10.5px] font-medium text-muted-foreground"
      style={{ ["--persona" as string]: `oklch(${accent})` }}
    >
      {children}
    </div>
  );
}

function ArchitectureView() {
  return (
    <div
      className="mx-auto max-w-5xl space-y-2"
      style={{ ["--persona" as string]: `oklch(${BLUE})` }}
    >
      {/* Intro */}
      <div className="animate-fade-up mb-2 text-center">
        <div className="persona-text mb-1 flex items-center justify-center gap-1.5 text-xs font-semibold uppercase tracking-widest">
          <Radio className="size-3.5" /> One app · the whole platform
        </div>
        <h2 className="gradient-text text-2xl font-semibold tracking-tight">
          How the Command Center runs on Databricks
        </h2>
        <p className="mx-auto mt-1 max-w-2xl text-sm text-muted-foreground">
          A single Databricks App unifies five platform pillars behind one governed,
          real-time experience — no data movement, no ungoverned AI.
        </p>
      </div>

      {/* Consumers */}
      <div
        className="animate-fade-up glass mx-auto flex max-w-2xl flex-col items-center gap-2 rounded-2xl p-4"
        style={{ animationDelay: "60ms" }}
      >
        <div className="flex items-center gap-2 text-sm font-medium">
          <Users className="persona-text size-4" /> Board & Executives
        </div>
        <div className="flex flex-wrap justify-center gap-1.5">
          {PERSONAS.map((p) => (
            <span
              key={p.id}
              className="rounded-full border border-border/60 bg-background/50 px-2.5 py-1 text-[11px] text-foreground/80"
              style={{ ["--persona" as string]: `oklch(${p.accent})` }}
            >
              {p.short}
            </span>
          ))}
        </div>
      </div>

      <FlowConnector height="h-12" />
      <ApiLabel accent={BLUE}>
        <span className="inline-flex items-center gap-1">
          <Lock className="size-3" /> HTTPS · SSO (OAuth)
        </span>
      </ApiLabel>
      <FlowConnector height="h-12" />

      {/* App node */}
      <div
        className="animate-fade-up glass-persona arch-glow mx-auto flex max-w-2xl flex-col items-center gap-3 rounded-2xl p-5 text-center"
        style={{ animationDelay: "160ms" }}
      >
        <div className="persona-bg-soft persona-text grid size-14 place-items-center rounded-2xl">
          <AppWindow className="size-7" />
        </div>
        <div>
          <div className="text-lg font-semibold">Executive Command Center</div>
          <div className="text-xs text-muted-foreground">
            Databricks App · apx (React + Vite + FastAPI)
          </div>
        </div>
        <div className="flex flex-wrap justify-center gap-1.5">
          {APP_BADGES.map((b) => (
            <span
              key={b}
              className="persona-bg-soft persona-text rounded-full px-2.5 py-1 text-[11px] font-medium"
            >
              {b}
            </span>
          ))}
        </div>
      </div>

      {/* Fan-out to pillars (desktop) */}
      <div className="hidden md:grid md:grid-cols-5 md:gap-4">
        {PILLARS.map((p) => (
          <div key={p.id} className="space-y-1.5">
            <FlowConnector accent={p.accent} height="h-10" packets={2} />
            <ApiLabel accent={p.accent}>{p.api}</ApiLabel>
            <FlowConnector accent={p.accent} height="h-6" packets={1} />
          </div>
        ))}
      </div>

      {/* Single connector (mobile) */}
      <div className="md:hidden">
        <FlowConnector height="h-10" />
        <div className="flex items-center justify-center gap-1 text-[11px] text-muted-foreground">
          <ArrowDown className="size-3.5" /> queries · governed AI · app state
        </div>
      </div>

      {/* Pillars */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
        {PILLARS.map((p, i) => (
          <PillarCard key={p.id} p={p} index={i} />
        ))}
      </div>

      {/* Governance ribbon */}
      <div
        className="animate-fade-up glass mt-4 flex flex-col gap-3 rounded-2xl p-4 sm:flex-row sm:items-center"
        style={{ animationDelay: "720ms" }}
      >
        <div className="flex items-center gap-2 text-sm font-semibold">
          <ShieldCheck className="size-4 text-emerald-400" /> Governed by design
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Every AI narrative and assistant call routes through the AI Gateway — PII
          masking, keyword filters, and rate limits — then writes an audit row to
          Lakebase and an inference record to the Lakehouse. Data reflects the lakehouse{" "}
          <span className="text-foreground/90">as of this morning</span>, not a day-late
          extract.
        </p>
      </div>
    </div>
  );
}
