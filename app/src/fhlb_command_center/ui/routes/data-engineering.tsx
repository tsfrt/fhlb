import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import {
  Workflow,
  Boxes,
  Layers,
  Sparkles,
  Database,
  ShieldCheck,
  Cpu,
  Users,
  GitBranch,
  ArrowRight,
  ArrowDown,
  RefreshCw,
  CheckCircle2,
  FileCode2,
  CircleDot,
  Radio,
} from "lucide-react";

export const Route = createFileRoute("/data-engineering")({ component: DataEngineeringView });

const BLUE = "0.72 0.14 233";

// Domain accents (kept in sync with the Data Model tab).
const ACCENT = {
  members: "0.72 0.14 233",
  advances: "0.74 0.13 205",
  collateral: "0.66 0.22 20",
  credit: "0.68 0.2 30",
  mortgage: "0.7 0.16 300",
  treasury: "0.62 0.16 275",
  planning: "0.7 0.12 195",
  mission: "0.75 0.15 155",
  engagement: "0.8 0.16 85",
  governance: "0.68 0.19 300",
} as const;

// ---------------------------------------------------------------------------
// Medallion reference architecture (Source Systems -> Bronze -> Silver -> Gold
// -> Consumers). Bronze/Silver are the reference ingestion pattern; Gold is the
// 38 governed materialized views the pipeline actually publishes.
// ---------------------------------------------------------------------------
type Layer = {
  id: string;
  name: string;
  kind: string;
  accent: string;
  icon: ReactNode;
  points: string[];
  tag: string;
};

const LAYERS: Layer[] = [
  {
    id: "bronze",
    name: "Bronze",
    kind: "Raw ingest",
    accent: "0.7 0.11 60",
    icon: <Boxes className="size-5" />,
    points: [
      "Append-only landing, schema-on-read",
      "Metadata stamped (_ingested_at, _source)",
      "Full source history preserved",
    ],
    tag: "raw",
  },
  {
    id: "silver",
    name: "Silver",
    kind: "Conformed",
    accent: "0.8 0.03 250",
    icon: <Layers className="size-5" />,
    points: [
      "Typed, validated, deduplicated",
      "Member & advance conformance",
      "Business rules + quality checks",
    ],
    tag: "cleansed",
  },
  {
    id: "gold",
    name: "Gold",
    kind: "Curated / serving",
    accent: "0.82 0.16 90",
    icon: <Sparkles className="size-5" />,
    points: [
      "38 governed tables in fhlb.des_moines",
      "10 business domains, members as spine",
      "Column comments preserved for Genie",
    ],
    tag: "materialized views",
  },
  {
    id: "consumers",
    name: "Consumers",
    kind: "Read-only",
    accent: BLUE,
    icon: <Users className="size-5" />,
    points: [
      "6 executive cockpits",
      "5 persona Genie spaces",
      "Member Early-Warning model + exam packs",
    ],
    tag: "governed reads",
  },
];

// ---------------------------------------------------------------------------
// The actual Lakeflow SDP pipeline: facts + dependency DAG.
// ---------------------------------------------------------------------------
const FACTS: { icon: ReactNode; label: string; value: string }[] = [
  { icon: <Workflow className="size-4" />, label: "Pipeline", value: "Lakeflow Spark Declarative Pipeline" },
  { icon: <Cpu className="size-4" />, label: "Compute", value: "Serverless" },
  { icon: <FileCode2 className="size-4" />, label: "Definition", value: "Python @dp.materialized_view" },
  { icon: <GitBranch className="size-4" />, label: "Deploy", value: "Databricks Asset Bundle (pipeline/)" },
  { icon: <Database className="size-4" />, label: "Target", value: "fhlb.des_moines" },
  { icon: <RefreshCw className="size-4" />, label: "Refresh", value: "Deterministic full refresh" },
  { icon: <CheckCircle2 className="size-4" />, label: "Gate", value: "--validate-only before publish" },
  { icon: <Layers className="size-4" />, label: "Outputs", value: "38 materialized views" },
];

type Node = { name: string; accent: string };

type Level = { id: string; label: string; blurb: string; nodes: Node[] };

const LEVELS: Level[] = [
  {
    id: "seeds",
    label: "Seeds",
    blurb: "Roots of the graph — generated first.",
    nodes: [
      { name: "members", accent: ACCENT.members },
      { name: "ops_source_systems", accent: ACCENT.governance },
      { name: "ops_model_inventory", accent: ACCENT.governance },
    ],
  },
  {
    id: "first",
    label: "First-order",
    blurb: "Derived directly from a seed.",
    nodes: [
      { name: "advance_daily_balances", accent: ACCENT.advances },
      { name: "advance_forecast_quarterly", accent: ACCENT.advances },
      { name: "letters_of_credit", accent: ACCENT.advances },
      { name: "member_credit_ratings", accent: ACCENT.credit },
      { name: "call_reports_quarterly", accent: ACCENT.credit },
      { name: "mortgage_originations", accent: ACCENT.mortgage },
      { name: "ahp_applications", accent: ACCENT.mission },
      { name: "homeownership_setaside", accent: ACCENT.mission },
      { name: "cip_cica_activity", accent: ACCENT.mission },
      { name: "eadvantage_activity", accent: ACCENT.engagement },
      { name: "ops_data_quality_exceptions", accent: ACCENT.governance },
      { name: "ops_column_lineage", accent: ACCENT.governance },
      { name: "ops_access_events", accent: ACCENT.governance },
    ],
  },
  {
    id: "downstream",
    label: "Downstream",
    blurb: "Built on a first-order table.",
    nodes: [
      { name: "pledged_collateral", accent: ACCENT.collateral },
      { name: "mpf_loans", accent: ACCENT.mortgage },
      { name: "mission_units", accent: ACCENT.mission },
      { name: "ops_gl_reconciliation", accent: ACCENT.governance },
    ],
  },
  {
    id: "final",
    label: "Final",
    blurb: "Deepest hop in the chain.",
    nodes: [{ name: "mpf_servicing_monthly", accent: ACCENT.mortgage }],
  },
];

// Independent roots (no upstream pipeline dependency).
const ROOTS: Node[] = [
  { name: "eligible_nonmembers", accent: ACCENT.members },
  { name: "collateral_reviews", accent: ACCENT.collateral },
  { name: "market_rates_daily", accent: ACCENT.treasury },
  { name: "advance_pricing_daily", accent: ACCENT.advances },
  { name: "co_issuances", accent: ACCENT.treasury },
  { name: "bank_position_daily", accent: ACCENT.treasury },
  { name: "investment_holdings", accent: ACCENT.treasury },
  { name: "prepayment_speeds", accent: ACCENT.treasury },
  { name: "financials_actual_vs_forecast", accent: ACCENT.planning },
  { name: "vendor_spend", accent: ACCENT.planning },
  { name: "capital_plan", accent: ACCENT.planning },
  { name: "pledge_activity", accent: ACCENT.mission },
  { name: "ops_bi_refresh", accent: ACCENT.governance },
  { name: "ops_metric_reconciliation", accent: ACCENT.governance },
  { name: "ops_examiner_requests", accent: ACCENT.governance },
  { name: "ops_pipeline_cost", accent: ACCENT.governance },
  { name: "ops_ai_content_sources", accent: ACCENT.governance },
];

// Signature chains — the specific edges worth calling out.
const CHAINS: { id: string; steps: Node[] }[] = [
  {
    id: "collateral",
    steps: [
      { name: "advance_daily_balances", accent: ACCENT.advances },
      { name: "pledged_collateral", accent: ACCENT.collateral },
    ],
  },
  {
    id: "mpf",
    steps: [
      { name: "mortgage_originations", accent: ACCENT.mortgage },
      { name: "mpf_loans", accent: ACCENT.mortgage },
      { name: "mpf_servicing_monthly", accent: ACCENT.mortgage },
    ],
  },
  {
    id: "lineage",
    steps: [
      { name: "ops_source_systems", accent: ACCENT.governance },
      { name: "ops_data_quality_exceptions", accent: ACCENT.governance },
    ],
  },
];

const TABLE_TOTAL =
  LEVELS.reduce((n, l) => n + l.nodes.length, 0) + ROOTS.length;

// ---------------------------------------------------------------------------
// Building blocks
// ---------------------------------------------------------------------------
function FlowConnector({
  accent = BLUE,
  height = "h-10",
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
        <span key={i} className="arch-packet" style={{ animationDelay: `${i * 1.2}s` }} />
      ))}
    </div>
  );
}

function NodeChip({ n, hub = false }: { n: Node; hub?: boolean }) {
  return (
    <span
      className={
        hub
          ? "persona-bg-soft persona-text persona-ring inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[12px] font-semibold"
          : "inline-flex items-center gap-1.5 rounded-lg border border-border/60 bg-background/50 px-2 py-1 text-[11px] text-foreground/85"
      }
      style={{ ["--persona" as string]: `oklch(${n.accent})` }}
    >
      <span
        className="size-1.5 shrink-0 rounded-full"
        style={{ background: `oklch(${n.accent})` }}
      />
      <code className="font-mono">{n.name}</code>
    </span>
  );
}

function LayerCard({ layer, index }: { layer: Layer; index: number }) {
  return (
    <div
      className="animate-fade-up glass-persona w-full rounded-2xl p-4"
      style={{
        ["--persona" as string]: `oklch(${layer.accent})`,
        animationDelay: `${120 + index * 90}ms`,
      }}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex items-center gap-3 sm:w-56 sm:shrink-0">
          <div className="persona-bg-soft persona-text arch-float grid size-11 place-items-center rounded-xl">
            {layer.icon}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold">{layer.name}</div>
            <div className="text-[11px] text-muted-foreground">{layer.kind}</div>
          </div>
        </div>
        <ul className="flex-1 grid gap-1.5 sm:grid-cols-2">
          {layer.points.map((pt) => (
            <li key={pt} className="flex items-start gap-2 text-xs text-foreground/85">
              <span className="persona-text mt-1 size-1.5 shrink-0 rounded-full bg-[var(--persona)]" />
              {pt}
            </li>
          ))}
        </ul>
        <span className="persona-bg-soft persona-text w-fit shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium">
          {layer.tag}
        </span>
      </div>
    </div>
  );
}

function LevelBand({ level, index }: { level: Level; index: number }) {
  return (
    <div
      className="animate-fade-up glass w-full rounded-2xl p-4"
      style={{ ["--persona" as string]: `oklch(${BLUE})`, animationDelay: `${120 + index * 80}ms` }}
    >
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <div className="text-sm font-semibold">{level.label}</div>
        <div className="text-[11px] text-muted-foreground">{level.blurb}</div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {level.nodes.map((n) => (
          <NodeChip key={n.name} n={n} hub={n.name === "members"} />
        ))}
      </div>
    </div>
  );
}

function Chain({ steps }: { steps: Node[] }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {steps.map((s, i) => (
        <span key={s.name} className="flex items-center gap-1.5">
          <NodeChip n={s} />
          {i < steps.length - 1 && (
            <ArrowRight className="size-3.5 shrink-0 text-muted-foreground" />
          )}
        </span>
      ))}
    </div>
  );
}

function Stat({ icon, value, label }: { icon: ReactNode; value: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="persona-text">{icon}</span>
      <div className="text-left leading-tight">
        <div className="text-sm font-semibold text-foreground">{value}</div>
        <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

function SectionHeading({
  kicker,
  title,
  icon,
}: {
  kicker: string;
  title: string;
  icon: ReactNode;
}) {
  return (
    <div className="animate-fade-up flex items-center gap-2 pt-2">
      <span className="persona-bg-soft persona-text grid size-8 place-items-center rounded-lg">
        {icon}
      </span>
      <div>
        <div className="persona-text text-[10.5px] font-semibold uppercase tracking-[0.14em]">
          {kicker}
        </div>
        <h3 className="text-base font-semibold leading-tight">{title}</h3>
      </div>
    </div>
  );
}

function DataEngineeringView() {
  return (
    <div
      className="mx-auto max-w-5xl space-y-4"
      style={{ ["--persona" as string]: `oklch(${BLUE})` }}
    >
      {/* Intro */}
      <div className="animate-fade-up text-center">
        <div className="persona-text mb-1 flex items-center justify-center gap-1.5 text-xs font-semibold uppercase tracking-widest">
          <Radio className="size-3.5" /> Declarative, governed, serverless
        </div>
        <h2 className="gradient-text text-2xl font-semibold tracking-tight">
          From source systems to serving, declaratively
        </h2>
        <p className="mx-auto mt-1 max-w-2xl text-sm text-muted-foreground">
          A single <span className="text-foreground/90">Lakeflow Spark Declarative Pipeline</span>{" "}
          rebuilds the entire <code className="text-foreground/90">fhlb.des_moines</code> data model
          as a dependency-tracked graph of materialized views — following the medallion pattern from
          raw ingest all the way to the cockpits.
        </p>
      </div>

      {/* Stat strip */}
      <div
        className="animate-fade-up glass mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-x-6 gap-y-2 rounded-2xl px-4 py-3 text-center"
        style={{ animationDelay: "60ms" }}
      >
        <Stat icon={<Layers className="size-4" />} value={`${TABLE_TOTAL}`} label="materialized views" />
        <Stat icon={<Workflow className="size-4" />} value="1" label="Lakeflow pipeline" />
        <Stat icon={<Boxes className="size-4" />} value="4" label="medallion stages" />
        <Stat icon={<Cpu className="size-4" />} value="Serverless" label="compute" />
      </div>

      {/* Section A — Medallion flow */}
      <SectionHeading
        kicker="Reference architecture"
        title="Medallion: raw to curated to served"
        icon={<Layers className="size-4" />}
      />
      <div className="space-y-1">
        {LAYERS.map((layer, i) => (
          <div key={layer.id}>
            <LayerCard layer={layer} index={i} />
            {i < LAYERS.length - 1 && (
              <FlowConnector accent={LAYERS[i + 1]!.accent} height="h-9" packets={2} />
            )}
          </div>
        ))}
      </div>

      {/* Section B — SDP pipeline facts */}
      <SectionHeading
        kicker="Implementation"
        title="The Lakeflow Spark Declarative Pipeline"
        icon={<Workflow className="size-4" />}
      />
      <div
        className="animate-fade-up glass-persona grid gap-x-6 gap-y-3 rounded-2xl p-4 sm:grid-cols-2"
        style={{ ["--persona" as string]: `oklch(${BLUE})`, animationDelay: "80ms" }}
      >
        {FACTS.map((f) => (
          <div key={f.label} className="flex items-center gap-2.5">
            <span className="persona-bg-soft persona-text grid size-8 shrink-0 place-items-center rounded-lg">
              {f.icon}
            </span>
            <div className="min-w-0 leading-tight">
              <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
                {f.label}
              </div>
              <div className="truncate text-[13px] font-medium text-foreground">{f.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Dependency DAG — leveled bands */}
      <div className="animate-fade-up flex items-center gap-2 pt-1 text-xs text-muted-foreground">
        <GitBranch className="persona-text size-3.5" /> Dependency graph — SDP tracks edges from{" "}
        <code className="text-foreground/80">spark.read.table(...)</code>, so it builds and refreshes in order.
      </div>
      <div className="space-y-1">
        {LEVELS.map((level, i) => (
          <div key={level.id}>
            <LevelBand level={level} index={i} />
            {i < LEVELS.length - 1 && <FlowConnector height="h-8" packets={2} />}
          </div>
        ))}
      </div>

      {/* Signature chains */}
      <div
        className="animate-fade-up glass rounded-2xl p-4"
        style={{ animationDelay: "120ms" }}
      >
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <CircleDot className="persona-text size-4" /> Signature chains
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {CHAINS.map((c) => (
            <Chain key={c.id} steps={c.steps} />
          ))}
        </div>
        <div className="mt-3 border-t border-border/50 pt-3 text-[11.5px] leading-relaxed text-muted-foreground">
          Plus <code className="text-foreground/80">members</code> fanning out to 11 domain tables,{" "}
          <code className="text-foreground/80">ops_model_inventory → member_credit_ratings</code>,{" "}
          <code className="text-foreground/80">ahp_applications → mission_units</code>, and{" "}
          <code className="text-foreground/80">eadvantage_activity → ops_gl_reconciliation</code>.
        </div>
      </div>

      {/* Independent roots */}
      <div
        className="animate-fade-up glass rounded-2xl p-4"
        style={{ animationDelay: "160ms" }}
      >
        <div className="mb-2 flex items-baseline justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Database className="persona-text size-4" /> Independent roots
          </div>
          <div className="text-[11px] text-muted-foreground">
            {ROOTS.length} reference / log tables with no upstream
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {ROOTS.map((n) => (
            <NodeChip key={n.name} n={n} />
          ))}
        </div>
      </div>

      {/* Governance ribbon */}
      <div
        className="animate-fade-up glass mt-2 flex flex-col gap-3 rounded-2xl p-4 sm:flex-row sm:items-center"
        style={{ animationDelay: "200ms" }}
      >
        <div className="flex items-center gap-2 text-sm font-semibold">
          <ShieldCheck className="size-4 text-emerald-400" /> Engineered for the exam
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Every table is a governed materialized view in Unity Catalog with column comments intact for
          Genie. Runs are deterministic and gated by a{" "}
          <code className="text-foreground/80">--validate-only</code> graph check before any publish,
          serverless compute scales to the job, and lineage is captured automatically — no overnight
          batch, no ungoverned copies.
        </p>
        <span className="persona-bg-soft persona-text flex items-center gap-1.5 self-start rounded-full px-2.5 py-1 text-[11px] font-medium sm:self-center">
          <ArrowDown className="size-3" /> feeds every cockpit
        </span>
      </div>
    </div>
  );
}
