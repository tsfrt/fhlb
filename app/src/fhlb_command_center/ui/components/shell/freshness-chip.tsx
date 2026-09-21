import { useFreshnessSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { QueryBoundary } from "@/components/common/query-boundary";

function Inner() {
  const { data } = useFreshnessSuspense(selector());
  return (
    <span className="tnum text-foreground/90">{data.as_of ?? "-"}</span>
  );
}

export function FreshnessChip() {
  return (
    <div className="glass flex items-center gap-2 rounded-full px-3 py-1.5 text-xs">
      <span className="live-dot size-2 rounded-full bg-emerald-400" />
      <span className="text-muted-foreground">Data as of</span>
      <QueryBoundary fallback={<span className="text-muted-foreground">…</span>}>
        <Inner />
      </QueryBoundary>
    </div>
  );
}
