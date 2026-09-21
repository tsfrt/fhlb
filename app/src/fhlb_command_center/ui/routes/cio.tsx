import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ShieldCheck,
  FileWarning,
  Timer,
  DollarSign,
  Boxes,
  KeyRound,
  GitBranch,
  FolderPlus,
  Plus,
  ArrowRight,
  FileText,
} from "lucide-react";
import {
  useCioDqExceptionsSuspense,
  useCioBiSlaSuspense,
  useCioDualRunCostSuspense,
  useCioModelBacklogSuspense,
  useCioAccessOobSuspense,
  useCioLineageSuspense,
  useListExamRequestsSuspense,
  useCreateExamRequest,
  useAddExamItem,
  listExamRequestsKey,
} from "@/lib/api";
import type { SafeRows } from "@/components/common/rows-view";
import selector from "@/lib/selector";
import { Panel } from "@/components/common/panel";
import { RowsBoundary } from "@/components/common/rows-view";
import { QueryBoundary } from "@/components/common/query-boundary";
import { AiBriefing } from "@/components/common/ai-briefing";
import { AnomalyRadar } from "@/components/common/anomaly-radar";
import { BarChartView, LineChartView } from "@/components/common/charts";
import { RowsTable } from "@/components/common/rows-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/cio")({ component: CioCockpit });

function DualRunChart({ data }: { data: SafeRows }) {
  const platforms = Array.from(new Set(data.rows.map((r) => String(r.platform))));
  const byMonth: Record<string, Record<string, number | string>> = {};
  for (const r of data.rows) {
    const m = String(r.month);
    byMonth[m] = byMonth[m] ?? { month: m };
    byMonth[m][String(r.platform)] = Number(r.cost_k) || 0;
  }
  return (
    <LineChartView
      data={Object.values(byMonth) as never}
      x="month"
      lines={platforms.map((p) => ({ key: p, name: p }))}
    />
  );
}

function LineageViewer() {
  const { data } = useCioLineageSuspense({ params: { field: "member_credit_rating" }, ...selector() });
  return (
    <div className="space-y-2">
      <div className="text-xs text-muted-foreground">
        Column lineage for <span className="persona-text font-medium">member_credit_rating</span>
      </div>
      <div className="flex flex-col gap-2">
        {(data.rows ?? []).map((r, i) => (
          <div key={i} className="glass flex flex-wrap items-center gap-2 rounded-lg p-2.5 text-xs">
            <Badge variant="outline" className="text-[10px]">{String(r.layer)}</Badge>
            <span className="font-medium">{String(r.system_name)}</span>
            {r.instance_label ? <span className="text-muted-foreground">({String(r.instance_label)})</span> : null}
            <span className="truncate">{String(r.upstream_object)}</span>
            <ArrowRight className="persona-text size-3.5" />
            <span className="truncate text-muted-foreground">{String(r.downstream_object)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ExamPack() {
  const { data } = useListExamRequestsSuspense(selector());
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [examiner, setExaminer] = useState("FHFA");
  const invalidate = () => qc.invalidateQueries({ queryKey: listExamRequestsKey() });
  const { mutate: create, isPending: creating } = useCreateExamRequest({
    mutation: {
      onSuccess: () => {
        invalidate();
        setTitle("");
        toast.success("Exam request created");
      },
    },
  });
  const { mutate: addItem } = useAddExamItem({
    mutation: { onSuccess: () => { invalidate(); toast.success("Evidence added"); } },
  });

  return (
    <div className="space-y-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!title.trim()) return;
          create({ params: {}, data: { title, examiner } });
        }}
        className="flex flex-wrap items-center gap-2"
      >
        <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Evidence pack title (e.g. Q3 FHFA exam - credit ratings)" className="flex-1 min-w-52" />
        <Input value={examiner} onChange={(e) => setExaminer(e.target.value)} placeholder="Examiner" className="w-28" />
        <Button type="submit" disabled={creating} className="gap-1.5">
          <FolderPlus className="size-4" /> Create
        </Button>
      </form>

      {!data.length && (
        <p className="py-6 text-center text-sm text-muted-foreground">
          No evidence packs yet. Create one to assemble examiner-ready artifacts.
        </p>
      )}

      <div className="space-y-2">
        {data.map((req) => (
          <div key={req.id} className="glass rounded-lg p-3">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <FileText className="persona-text size-4" />
                <span className="text-sm font-medium">{req.title}</span>
                <Badge variant="outline" className="text-[10px]">{req.examiner}</Badge>
                <Badge variant="secondary" className="text-[10px]">{req.status}</Badge>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 gap-1 text-xs"
                onClick={() =>
                  addItem({
                    params: { req_id: req.id },
                    data: {
                      label: `Open DQ exceptions snapshot (${new Date().toISOString().slice(0, 10)})`,
                      source_type: "lakehouse",
                      source_ref: "fhlb.des_moines.ops_data_quality_exceptions",
                    },
                  })
                }
              >
                <Plus className="size-3.5" /> Add evidence
              </Button>
            </div>
            {(req.items ?? []).length > 0 && (
              <ul className="mt-2 space-y-1 border-t border-border/40 pt-2">
                {(req.items ?? []).map((it) => (
                  <li key={it.id} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Boxes className="size-3.5" />
                    <span className="text-foreground/80">{it.label}</span>
                    <span className="opacity-60">· {it.source_ref}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CioCockpit() {
  return (
    <div className="space-y-5">
      <AiBriefing persona="cio" title="Governance & operations briefing" />
      <AnomalyRadar persona="cio" />
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title="Open FHFA Data Quality Exceptions" subtitle="Traced to source SQL Server instance" icon={<FileWarning className="size-4" />} persona className="lg:col-span-2">
          <RowsBoundary hook={useCioDqExceptionsSuspense as never} render={(d) => <RowsTable columns={d.columns} rows={d.rows} maxHeight="280px" />} />
        </Panel>

        <Panel title="Dual-Run Platform Cost" subtitle="SQL Server / Qlik vs Fabric migration, monthly" icon={<DollarSign className="size-4" />}>
          <RowsBoundary hook={useCioDualRunCostSuspense as never} render={(d) => <DualRunChart data={d} />} />
        </Panel>

        <Panel title="BI Refresh SLA" subtitle="Refreshes and SLA misses by tool" icon={<Timer className="size-4" />}>
          <RowsBoundary
            hook={useCioBiSlaSuspense as never}
            render={(d) => (
              <BarChartView data={d.rows} x="bi_tool" bars={[{ key: "refreshes", name: "Refreshes" }, { key: "sla_misses", name: "SLA misses" }]} />
            )}
          />
        </Panel>

        <Panel title="Model Validation Backlog" subtitle="Overdue or unvalidated models" icon={<Boxes className="size-4" />}>
          <RowsBoundary hook={useCioModelBacklogSuspense as never} render={(d) => <RowsTable columns={d.columns} rows={d.rows} maxHeight="240px" />} />
        </Panel>

        <Panel title="Out-of-Policy Access" subtitle="Access events breaching data classification policy" icon={<KeyRound className="size-4" />}>
          <RowsBoundary hook={useCioAccessOobSuspense as never} render={(d) => <RowsTable columns={d.columns} rows={d.rows} maxHeight="240px" />} />
        </Panel>

        <Panel title="Lineage Viewer" subtitle="End-to-end lineage for a regulated field" icon={<GitBranch className="size-4" />} persona>
          <QueryBoundary fallback={<Skeleton className="h-56 w-full" />}>
            <LineageViewer />
          </QueryBoundary>
        </Panel>

        <Panel title="Examiner Evidence Pack" subtitle="Assemble & persist artifacts in Lakebase" icon={<ShieldCheck className="size-4" />}>
          <QueryBoundary fallback={<Skeleton className="h-56 w-full" />}>
            <ExamPack />
          </QueryBoundary>
        </Panel>
      </div>

    </div>
  );
}
