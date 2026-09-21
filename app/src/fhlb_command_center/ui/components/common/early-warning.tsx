import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Activity,
  ChevronDown,
  Plus,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  useCroEarlyWarningSuspense,
  croEarlyWarning,
  croEarlyWarningKey,
  useAddWatchlist,
  listWatchlistKey,
  type EarlyWarningItem,
} from "@/lib/api";
import selector from "@/lib/selector";
import { Panel } from "@/components/common/panel";
import { QueryBoundary } from "@/components/common/query-boundary";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { fmtNum } from "@/lib/format";

const BAND_STYLES: Record<string, string> = {
  High: "border-rose-500/40 text-rose-300 bg-rose-500/10",
  Elevated: "border-amber-500/40 text-amber-300 bg-amber-500/10",
  Low: "border-emerald-500/40 text-emerald-300 bg-emerald-500/10",
};

const BAND_BAR: Record<string, string> = {
  High: "bg-rose-500",
  Elevated: "bg-amber-500",
  Low: "bg-emerald-500",
};

function pctLabel(pd: number): string {
  return `${Math.round(pd * 100)}%`;
}

function DriverRow({ label, direction, value }: { label: string; direction: string; value: number | null | undefined }) {
  const up = direction === "increases risk";
  return (
    <div className="flex items-center gap-2 text-xs">
      {up ? (
        <ArrowUpRight className="size-3.5 text-rose-400" />
      ) : (
        <ArrowDownRight className="size-3.5 text-emerald-400" />
      )}
      <span className="text-foreground/90">{label}</span>
      <span className="text-muted-foreground">
        {value === null || value === undefined ? "" : `· ${fmtNum(value, 2)}`}
      </span>
      <span className={cn("ml-auto", up ? "text-rose-300" : "text-emerald-300")}>
        {up ? "raises" : "lowers"} PD
      </span>
    </div>
  );
}

function Item({ item }: { item: EarlyWarningItem }) {
  const [open, setOpen] = useState(false);
  const qc = useQueryClient();
  const { mutate, isPending } = useAddWatchlist({
    mutation: {
      onSuccess: () => {
        qc.invalidateQueries({ queryKey: listWatchlistKey() });
        toast.success(`${item.member_name} added to watchlist`);
      },
    },
  });

  const band = item.risk_band ?? "Low";
  const drivers = item.drivers ?? [];

  return (
    <div className="glass rounded-lg">
      <div className="flex items-center gap-3 px-3 py-2">
        <button
          className="flex min-w-0 flex-1 items-center gap-3 text-left"
          onClick={() => setOpen((v) => !v)}
        >
          <ChevronDown
            className={cn("size-4 shrink-0 text-muted-foreground transition", open && "rotate-180")}
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-medium">{item.member_name}</span>
              {item.rating_gap && (
                <Badge variant="outline" className="border-rose-500/50 bg-rose-500/15 text-[10px] text-rose-200">
                  RATING GAP
                </Badge>
              )}
            </div>
            <div className="text-xs text-muted-foreground">
              {item.internal_rating ?? "-"} · ${fmtNum(item.advances_mm, 1)}M advances
            </div>
          </div>
        </button>

        <div className="hidden w-40 items-center gap-2 sm:flex">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted/40">
            <div
              className={cn("h-full rounded-full", BAND_BAR[band] ?? BAND_BAR.Low)}
              style={{ width: `${Math.max(4, Math.round(item.pd_12m * 100))}%` }}
            />
          </div>
          <span className="w-9 text-right text-xs tabular-nums text-foreground/90">
            {pctLabel(item.pd_12m)}
          </span>
        </div>

        <Badge variant="outline" className={cn("shrink-0 text-[10px]", BAND_STYLES[band] ?? BAND_STYLES.Low)}>
          {band}
        </Badge>

        <Button
          size="icon"
          variant="ghost"
          className="size-7 shrink-0"
          disabled={isPending}
          title="Add to watchlist"
          onClick={() =>
            mutate({
              params: {},
              data: {
                member_id: item.member_id,
                member_name: item.member_name,
                reason: `Early-warning PD ${pctLabel(item.pd_12m)} (${band})${item.rating_gap ? " · rating gap" : ""}`,
                severity: band === "High" ? "high" : band === "Elevated" ? "medium" : "low",
              },
            })
          }
        >
          <Plus className="size-4" />
        </Button>
      </div>

      {open && (
        <div className="space-y-1.5 border-t border-border/50 px-3 py-2.5">
          <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Top model drivers
          </div>
          {drivers.length ? (
            drivers.map((d, i) => (
              <DriverRow key={i} label={d.label} direction={d.direction} value={d.value} />
            ))
          ) : (
            <div className="text-xs text-muted-foreground">No driver detail.</div>
          )}
          <div className="pt-1 text-[11px] text-muted-foreground">
            Recommended: <span className="text-foreground/80">{item.recommended_action}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function Board() {
  const qc = useQueryClient();
  const { data } = useCroEarlyWarningSuspense(selector());
  const [rescoring, setRescoring] = useState(false);
  const items = data.items ?? [];

  async function rescore() {
    setRescoring(true);
    try {
      await croEarlyWarning({ refresh: true });
      await qc.invalidateQueries({ queryKey: croEarlyWarningKey() });
      toast.success("Rescored live via Model Serving");
    } catch {
      toast.error("Rescoring failed");
    } finally {
      setRescoring(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <Badge variant="outline" className="gap-1 border-border/60">
          <Activity className="size-3 persona-text" />
          {data.endpoint}
          {data.model_version ? ` · v${data.model_version}` : ""}
        </Badge>
        <span className="text-rose-300">{data.high ?? 0} high</span>
        <span>·</span>
        <span className="text-amber-300">{data.elevated ?? 0} elevated</span>
        <span>·</span>
        <span className="text-rose-200">{data.rating_gaps ?? 0} rating gaps</span>
        <Button
          size="sm"
          variant="ghost"
          className="ml-auto h-7 gap-1.5 text-xs"
          onClick={rescore}
          disabled={rescoring}
        >
          <RefreshCw className={cn("size-3.5", rescoring && "animate-spin")} />
          {data.cached ? "Rescore" : "Live"}
        </Button>
      </div>

      <div className="max-h-[26rem] space-y-1.5 overflow-auto pr-1">
        {items.length ? (
          items.map((it) => <Item key={it.member_id} item={it} />)
        ) : (
          <p className="py-8 text-center text-sm text-muted-foreground">No members scored.</p>
        )}
      </div>
    </div>
  );
}

export function EarlyWarningBoard() {
  return (
    <Panel
      title="Member Early-Warning (ML)"
      subtitle="12-month deterioration PD · Databricks Model Serving"
      icon={<Activity className="size-4" />}
      persona
      className="lg:col-span-2"
    >
      <QueryBoundary fallback={<Skeleton className="h-80 w-full" />}>
        <Board />
      </QueryBoundary>
    </Panel>
  );
}
