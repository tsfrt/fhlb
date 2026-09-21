import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  Banknote,
  Target,
  Home,
  FileWarning,
  AlertOctagon,
  BellRing,
  Check,
  ChevronDown,
} from "lucide-react";
import {
  useOverviewKpisSuspense,
  useOverviewDistrictSuspense,
  useOverviewAlertsSuspense,
  useAckAlert,
} from "@/lib/api";
import selector from "@/lib/selector";
import { QueryBoundary } from "@/components/common/query-boundary";
import { KpiCard } from "@/components/common/kpi-card";
import { Panel } from "@/components/common/panel";
import { AiBriefing } from "@/components/common/ai-briefing";
import { AnomalyRadar } from "@/components/common/anomaly-radar";
import { DistrictMap } from "@/components/common/district-map";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fmtInt, fmtNum } from "@/lib/format";

export const Route = createFileRoute("/")({
  component: Overview,
});

function KpiBand() {
  const { data } = useOverviewKpisSuspense(selector());
  const r = (data.rows ?? [])[0] ?? {};
  const cards = [
    { label: "Total Advances", value: `$${fmtNum(r.total_advances_bn, 1)}B`, icon: <Banknote className="size-4" />, sublabel: "Outstanding par, live" },
    { label: "Core Mission Ratio", value: `${fmtNum(r.core_mission_ratio_pct, 1)}%`, icon: <Target className="size-4" />, sublabel: "(Advances + AMA) / CO" },
    { label: "$200M Pledge YTD", value: `$${fmtNum(r.pledge_ytd_mm, 1)}M`, icon: <Home className="size-4" />, sublabel: "Disbursed this year" },
    { label: "Open Exam Exceptions", value: fmtInt(r.open_exceptions), icon: <FileWarning className="size-4" />, tone: "warn" as const, sublabel: "FHFA data quality" },
    { label: "At-Risk Members", value: fmtInt(r.at_risk_members), icon: <AlertOctagon className="size-4" />, tone: "bad" as const, sublabel: "Rating cadence breached" },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      {cards.map((c, i) => (
        <KpiCard key={c.label} {...c} delay={i * 60} />
      ))}
    </div>
  );
}

function DistrictPanel() {
  const { data } = useOverviewDistrictSuspense(selector());
  return <DistrictMap rows={data.rows as never} />;
}

const SEV_STYLE: Record<string, string> = {
  high: "border-rose-500/40 text-rose-300",
  medium: "border-amber-500/40 text-amber-300",
  low: "border-emerald-500/40 text-emerald-300",
};

function AlertFeed() {
  const { data } = useOverviewAlertsSuspense(selector());
  const [acked, setAcked] = useState<Set<string>>(new Set());
  const { mutate } = useAckAlert();
  const ack = (key: string, persona: string) => {
    setAcked((s) => new Set(s).add(key));
    mutate({ params: {}, data: { alert_key: key, persona } });
  };
  return (
    <div className="space-y-2">
      {(data.rows ?? []).map((a, i) => {
        const key = `${a.persona}:${a.title}:${a.detail}`.slice(0, 120);
        return (
          <AlertRow
            key={i}
            a={a}
            index={i}
            done={acked.has(key)}
            onAck={() => ack(key, String(a.persona))}
          />
        );
      })}
    </div>
  );
}

function AlertRow({
  a,
  index,
  done,
  onAck,
}: {
  a: Record<string, unknown>;
  index: number;
  done: boolean;
  onAck: () => void;
}) {
  const [open, setOpen] = useState(false);
  const detail = String(a.detail ?? "");
  return (
    <div
      className="glass flex items-start gap-3 rounded-lg p-3 animate-fade-up"
      style={{ animationDelay: `${index * 40}ms` }}
    >
      <BellRing className={`mt-0.5 size-4 ${SEV_STYLE[String(a.severity)]?.split(" ")[1] ?? ""}`} />
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="min-w-0 flex-1 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{String(a.title)}</span>
          <Badge variant="outline" className="text-[10px]">{String(a.persona)}</Badge>
          <Badge variant="outline" className={`text-[10px] ${SEV_STYLE[String(a.severity)] ?? ""}`}>
            {String(a.severity)}
          </Badge>
          <ChevronDown
            className={`ml-auto size-3.5 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>
        <p className={`text-xs text-muted-foreground ${open ? "mt-1 whitespace-pre-wrap" : "truncate"}`}>
          {detail}
        </p>
      </button>
      <Button
        size="sm"
        variant={done ? "secondary" : "ghost"}
        className="h-7 shrink-0 text-xs"
        disabled={done}
        onClick={onAck}
      >
        {done ? <><Check className="size-3.5" /> Ack'd</> : "Acknowledge"}
      </Button>
    </div>
  );
}

function Overview() {
  return (
    <div className="space-y-5">
      <QueryBoundary fallback={<Skeleton className="h-28 w-full" />}>
        <KpiBand />
      </QueryBoundary>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-5">
          <AiBriefing persona="overview" />
          <AnomalyRadar persona="overview" />
          <Panel title="District at a glance" subtitle="13 states + 3 Pacific territories · advances by charter state" persona>
            <QueryBoundary fallback={<Skeleton className="h-72 w-full" />}>
              <DistrictPanel />
            </QueryBoundary>
          </Panel>
        </div>

        <Panel
          title="Live alert feed"
          subtitle="Acknowledgements persist to Lakebase"
          icon={<BellRing className="size-4" />}
        >
          <QueryBoundary fallback={<Skeleton className="h-72 w-full" />}>
            <AlertFeed />
          </QueryBoundary>
        </Panel>
      </div>
    </div>
  );
}
