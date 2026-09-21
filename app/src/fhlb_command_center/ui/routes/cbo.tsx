import { createFileRoute } from "@tanstack/react-router";
import { BarChart3, PackageOpen, MousePointerClick, Sparkles, Boxes } from "lucide-react";
import {
  useCboUtilizationSuspense,
  useCboUnusedCapacitySuspense,
  useCboMpfLeakageSuspense,
  useCboEadvantageLurkersSuspense,
  useCboProspectsSuspense,
} from "@/lib/api";
import { Panel } from "@/components/common/panel";
import { RowsBoundary } from "@/components/common/rows-view";
import { AiBriefing } from "@/components/common/ai-briefing";
import { AnomalyRadar } from "@/components/common/anomaly-radar";
import { BarChartView, DonutChartView } from "@/components/common/charts";
import { RowsTable } from "@/components/common/rows-table";

export const Route = createFileRoute("/cbo")({ component: CboCockpit });

function CboCockpit() {
  return (
    <div className="space-y-5">
      <AiBriefing persona="cbo" title="Member growth briefing" />
      <AnomalyRadar persona="cbo" />
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title="Advance Utilization by Product" subtitle="Outstanding balance by advance type" icon={<Boxes className="size-4" />} persona>
          <RowsBoundary
            hook={useCboUtilizationSuspense as never}
            render={(d) => <DonutChartView data={d.rows} nameKey="product" valueKey="balance_bn" />}
          />
        </Panel>

        <Panel title="Unused Borrowing Capacity" subtitle="Whitespace: lendable collateral minus advances" icon={<BarChart3 className="size-4" />}>
          <RowsBoundary
            hook={useCboUnusedCapacitySuspense as never}
            render={(d) => (
              <BarChartView data={d.rows.slice(0, 10)} x="member_name" bars={[{ key: "unused_capacity_mm", name: "Unused ($M)" }]} height={260} />
            )}
          />
        </Panel>

        <Panel title="MPF Leakage" subtitle="Originations sold to outlets other than MPF" icon={<PackageOpen className="size-4" />} persona>
          <RowsBoundary
            hook={useCboMpfLeakageSuspense as never}
            render={(d) => <RowsTable columns={d.columns} rows={d.rows} maxHeight="260px" />}
          />
        </Panel>

        <Panel title="eAdvantage Lurkers" subtitle="Active on the portal but not transacting" icon={<MousePointerClick className="size-4" />}>
          <RowsBoundary
            hook={useCboEadvantageLurkersSuspense as never}
            render={(d) => <RowsTable columns={d.columns} rows={d.rows} maxHeight="260px" />}
          />
        </Panel>

        <Panel title="Prospect Lookalikes" subtitle="Eligible non-members ranked by similarity to your best members" icon={<Sparkles className="size-4" />} className="lg:col-span-2" persona>
          <RowsBoundary
            hook={useCboProspectsSuspense as never}
            render={(d) => <RowsTable columns={d.columns} rows={d.rows} maxHeight="300px" />}
          />
        </Panel>
      </div>

    </div>
  );
}
