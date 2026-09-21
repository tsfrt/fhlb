import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  HeartHandshake,
  Home,
  Filter,
  Coins,
  ShieldCheck,
  Send,
  Loader2,
  BadgeCheck,
} from "lucide-react";
import {
  useMissionPledgeSuspense,
  useMissionAhpFunnelSuspense,
  useMissionSubsidyEfficiencySuspense,
  useMissionUnitsByTierSuspense,
  useAiGovernanceSuspense,
  useAiAssistant,
  type GovernedResponse,
} from "@/lib/api";
import selector from "@/lib/selector";
import { Panel } from "@/components/common/panel";
import { RowsBoundary } from "@/components/common/rows-view";
import { QueryBoundary } from "@/components/common/query-boundary";
import { AnomalyRadar } from "@/components/common/anomaly-radar";
import { BarChartView } from "@/components/common/charts";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fmtNum } from "@/lib/format";

export const Route = createFileRoute("/mission")({ component: MissionCockpit });

const GOAL_MM = 200;

function PledgeGauge() {
  const { data } = useMissionPledgeSuspense(selector());
  const rows = data.rows ?? [];
  const disbursed = rows.reduce((a, r) => a + (Number(r.disbursed_mm) || 0), 0);
  const committed = rows.reduce((a, r) => a + (Number(r.committed_mm) || 0), 0);
  const pct = Math.min(100, (disbursed / GOAL_MM) * 100);
  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs text-muted-foreground">Disbursed YTD</div>
          <div className="tnum persona-text text-4xl font-semibold">${fmtNum(disbursed, 1)}M</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted-foreground">of pledge</div>
          <div className="tnum text-2xl font-semibold">${GOAL_MM}M</div>
        </div>
      </div>
      <Progress value={pct} className="h-3" />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{fmtNum(pct, 1)}% of goal</span>
        <span>${fmtNum(committed, 1)}M committed</span>
      </div>
      <BarChartView
        data={rows}
        x="program"
        bars={[
          { key: "committed_mm", name: "Committed ($M)" },
          { key: "disbursed_mm", name: "Disbursed ($M)" },
        ]}
        height={200}
      />
    </div>
  );
}

function GovernedAssistant() {
  const { data: gov } = useAiGovernanceSuspense(selector());
  const [q, setQ] = useState("");
  const [res, setRes] = useState<GovernedResponse | null>(null);
  const { mutate, isPending } = useAiAssistant({
    mutation: { onSuccess: (r) => setRes(r.data) },
  });
  const sources = gov.content_sources ?? [];
  const approved = sources.filter((s) => (s as { governed_flag?: boolean }).governed_flag);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <Badge variant="outline" className="gap-1 border-emerald-500/40 text-emerald-300">
          <ShieldCheck className="size-3" /> Governed via {gov.endpoint}
        </Badge>
        {gov.usage_tracking && <Badge variant="outline">usage tracked</Badge>}
        {gov.inference_table && <Badge variant="outline">inference table on</Badge>}
      </div>

      <p className="text-xs text-muted-foreground">
        Unlike the current ungoverned virtual assistant, this one only answers from
        {" "}
        <span className="persona-text font-medium">{approved.length}</span> approved content sources,
        masks PII, and writes an audit row to Lakebase for every answer.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!q.trim()) return;
          setRes(null);
          mutate({ question: q, persona: "mission" });
        }}
        className="flex items-center gap-2"
      >
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about AHP eligibility, subsidy limits, deadlines…" />
        <Button type="submit" disabled={isPending} className="gap-1.5">
          {isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          Ask
        </Button>
      </form>

      {res && (
        <div className="glass-persona animate-fade-up rounded-lg p-3">
          <p className="text-sm leading-relaxed">{res.content}</p>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
            <span>guardrails: <span className="text-emerald-300">{res.guardrail_verdict}</span></span>
            {res.latency_ms != null && <span>{res.latency_ms} ms</span>}
            <span className="opacity-70">audited to Lakebase</span>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border/50 p-3">
        <div className="mb-2 flex items-center gap-1.5 text-xs font-medium">
          <BadgeCheck className="size-3.5 text-emerald-400" /> Approved content sources
        </div>
        <div className="flex flex-wrap gap-1.5">
          {sources.map((s, i) => {
            const src = s as { content_source?: string; governed_flag?: boolean };
            return (
              <span
                key={i}
                className={`rounded-md border px-2 py-0.5 text-[11px] ${
                  src.governed_flag
                    ? "border-emerald-500/40 text-emerald-300"
                    : "border-rose-500/40 text-rose-300 line-through opacity-70"
                }`}
              >
                {src.content_source}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function MissionCockpit() {
  return (
    <div className="space-y-5">
      <AnomalyRadar persona="mission" />
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title="$200M Affordable Housing Pledge" subtitle="Year-to-date progress by program" icon={<Home className="size-4" />} persona>
          <QueryBoundary fallback={<Skeleton className="h-80 w-full" />}>
            <PledgeGauge />
          </QueryBoundary>
        </Panel>

        <Panel title="Governed Affordable Housing Assistant" subtitle="AI Gateway · approved sources only" icon={<ShieldCheck className="size-4" />}>
          <QueryBoundary fallback={<Skeleton className="h-80 w-full" />}>
            <GovernedAssistant />
          </QueryBoundary>
        </Panel>

        <Panel title="AHP Funnel" subtitle="Applications by status" icon={<Filter className="size-4" />}>
          <RowsBoundary
            hook={useMissionAhpFunnelSuspense as never}
            render={(d) => (
              <BarChartView data={d.rows} x="status" bars={[{ key: "applications", name: "Applications" }]} />
            )}
          />
        </Panel>

        <Panel title="Subsidy Efficiency" subtitle="Average subsidy per unit by project type" icon={<Coins className="size-4" />} persona>
          <RowsBoundary
            hook={useMissionSubsidyEfficiencySuspense as never}
            render={(d) => (
              <BarChartView data={d.rows} x="project_type" bars={[{ key: "avg_subsidy_per_unit", name: "$ / unit" }]} />
            )}
          />
        </Panel>

        <Panel title="Units by Income Tier" subtitle="Affordable units delivered, rural vs non-rural" icon={<HeartHandshake className="size-4" />} className="lg:col-span-2">
          <RowsBoundary
            hook={useMissionUnitsByTierSuspense as never}
            render={(d) => {
              const tiers: Record<string, Record<string, number | string>> = {};
              for (const r of d.rows) {
                const t = String(r.income_tier);
                tiers[t] = tiers[t] ?? { income_tier: t, Rural: 0, "Non-rural": 0 };
                const key = r.rural_flag ? "Rural" : "Non-rural";
                tiers[t][key] = ((tiers[t][key] as number) || 0) + (Number(r.units) || 0);
              }
              return (
                <BarChartView
                  data={Object.values(tiers) as never}
                  x="income_tier"
                  stacked
                  bars={[{ key: "Rural", name: "Rural" }, { key: "Non-rural", name: "Non-rural" }]}
                />
              );
            }}
          />
        </Panel>
      </div>

    </div>
  );
}
