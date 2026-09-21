import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Gauge, ShieldAlert, PieChart, TrendingDown, Star, X, Plus } from "lucide-react";
import { toast } from "sonner";
import {
  useCroRatingsOverdueSuspense,
  useCroOcCushionSuspense,
  useCroConcentrationSuspense,
  useCroMpfDelinquencySuspense,
  useListWatchlistSuspense,
  useAddWatchlist,
  useRemoveWatchlist,
  listWatchlistKey,
} from "@/lib/api";
import type { SafeRows } from "@/components/common/rows-view";
import selector from "@/lib/selector";
import { Panel } from "@/components/common/panel";
import { RowsBoundary } from "@/components/common/rows-view";
import { QueryBoundary } from "@/components/common/query-boundary";
import { AiBriefing } from "@/components/common/ai-briefing";
import { AnomalyRadar } from "@/components/common/anomaly-radar";
import { EarlyWarningBoard } from "@/components/common/early-warning";
import { BarChartView } from "@/components/common/charts";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fmtNum } from "@/lib/format";

export const Route = createFileRoute("/cro")({ component: CroCockpit });

function RatingsTable({ data }: { data: SafeRows }) {
  const qc = useQueryClient();
  const { mutate } = useAddWatchlist({
    mutation: {
      onSuccess: () => {
        qc.invalidateQueries({ queryKey: listWatchlistKey() });
        toast.success("Added to watchlist");
      },
    },
  });
  return (
    <div className="max-h-80 space-y-1.5 overflow-auto pr-1">
      {data.rows.map((r, i) => (
        <div key={i} className="glass flex items-center gap-3 rounded-lg px-3 py-2">
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium">{String(r.member_name)}</div>
            <div className="text-xs text-muted-foreground">
              {String(r.internal_rating)} · {fmtNum(r.days_overdue, 0)}d overdue · ${fmtNum(r.advances_mm, 1)}M
            </div>
          </div>
          <Badge variant="outline" className="border-rose-500/40 text-rose-300">{String(r.internal_rating)}</Badge>
          <Button
            size="icon"
            variant="ghost"
            className="size-7"
            onClick={() =>
              mutate({
                params: {},
                data: {
                  member_id: String(r.member_id),
                  member_name: String(r.member_name),
                  reason: `Rating ${r.internal_rating}, ${fmtNum(r.days_overdue, 0)}d past cadence`,
                  severity: "high",
                },
              })
            }
          >
            <Plus className="size-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}

function Watchlist() {
  const { data } = useListWatchlistSuspense(selector());
  const qc = useQueryClient();
  const { mutate } = useRemoveWatchlist({
    mutation: {
      onSuccess: () => qc.invalidateQueries({ queryKey: listWatchlistKey() }),
    },
  });
  if (!data.length)
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No members watchlisted yet. Add one from the overdue-ratings panel.
      </p>
    );
  return (
    <div className="space-y-1.5">
      {data.map((w) => (
        <div key={w.id} className="glass flex items-center gap-3 rounded-lg px-3 py-2">
          <Star className="persona-text size-4" />
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium">{w.member_name}</div>
            <div className="truncate text-xs text-muted-foreground">{w.reason}</div>
          </div>
          <Badge variant="outline" className="text-[10px]">{w.severity}</Badge>
          <Button size="icon" variant="ghost" className="size-7" onClick={() => mutate({ params: { item_id: w.id } })}>
            <X className="size-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}

function CroCockpit() {
  return (
    <div className="space-y-5">
      <AiBriefing persona="cro" title="Credit risk briefing" />
      <AnomalyRadar persona="cro" />
      <div className="grid gap-5 lg:grid-cols-2">
        <EarlyWarningBoard />

        <Panel title="Ratings past AB 2024-03 cadence" subtitle="Ranked by advances outstanding · add to watchlist" icon={<ShieldAlert className="size-4" />} persona>
          <RowsBoundary hook={useCroRatingsOverdueSuspense as never} render={(d) => <RatingsTable data={d} />} />
        </Panel>

        <Panel title="Member Watchlist" subtitle="Persisted in Lakebase (Postgres)" icon={<Star className="size-4" />}>
          <QueryBoundary fallback={<Skeleton className="h-64 w-full" />}>
            <Watchlist />
          </QueryBoundary>
        </Panel>

        <Panel title="Thinning OC Cushion" subtitle="Lendable vs advances · lowest cushion first" icon={<TrendingDown className="size-4" />}>
          <RowsBoundary
            hook={useCroOcCushionSuspense as never}
            render={(d) => (
              <BarChartView data={d.rows.slice(0, 10)} x="member_name" bars={[{ key: "oc_cushion_pct", name: "OC cushion %" }]} height={260} />
            )}
          />
        </Panel>

        <Panel title="Advance Concentration" subtitle="Top-10 members as % of book" icon={<PieChart className="size-4" />} persona>
          <RowsBoundary
            hook={useCroConcentrationSuspense as never}
            render={(d) => (
              <BarChartView data={d.rows} x="member_name" bars={[{ key: "pct_of_book", name: "% of book" }]} height={260} />
            )}
          />
        </Panel>

        <Panel title="MPF Delinquency & UPB Trend" subtitle="By delinquency bucket, trailing 12 months" icon={<Gauge className="size-4" />} className="lg:col-span-2">
          <RowsBoundary
            hook={useCroMpfDelinquencySuspense as never}
            render={(d) => {
              const buckets = Array.from(new Set(d.rows.map((r) => String(r.delinquency_bucket))));
              const byMonth: Record<string, Record<string, number>> = {};
              for (const r of d.rows) {
                const m = String(r.month);
                byMonth[m] = byMonth[m] ?? { month: m } as never;
                byMonth[m][String(r.delinquency_bucket)] = Number(r.upb_mm) || 0;
              }
              const rows = Object.values(byMonth);
              return (
                <BarChartView
                  data={rows as never}
                  x="month"
                  stacked
                  bars={buckets.map((b) => ({ key: b, name: b }))}
                  height={260}
                />
              );
            }}
          />
        </Panel>
      </div>

    </div>
  );
}
