import type { ReactNode } from "react";
import selector from "@/lib/selector";
import type { Rows } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { QueryBoundary } from "./query-boundary";

export interface SafeRows {
  columns: string[];
  rows: Record<string, unknown>[];
}

type RowsHook = (options?: unknown) => { data: Rows };

function normalize(data: Rows): SafeRows {
  return { columns: data.columns ?? [], rows: (data.rows ?? []) as Record<string, unknown>[] };
}

/**
 * Generic bridge for the auto-generated "*Suspense" hooks that all return Rows.
 * Normalizes optional fields so render callbacks get guaranteed arrays.
 */
export function RowsView({
  hook,
  render,
  options,
}: {
  hook: RowsHook;
  render: (data: SafeRows) => ReactNode;
  options?: Record<string, unknown>;
}) {
  const { data } = hook({ ...(options ?? {}), ...selector() });
  return <>{render(normalize(data))}</>;
}

export function RowsBoundary({
  hook,
  render,
  options,
  height = "18rem",
}: {
  hook: RowsHook;
  render: (data: SafeRows) => ReactNode;
  options?: Record<string, unknown>;
  height?: string;
}) {
  return (
    <QueryBoundary fallback={<Skeleton className="w-full" style={{ height }} />}>
      <RowsView hook={hook} render={render} options={options} />
    </QueryBoundary>
  );
}
