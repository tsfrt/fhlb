import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Landmark, Target, Waves, TrendingUp, Layers } from "lucide-react";
import {
  useCfoAdvancesVsForecastSuspense,
  useCfoCoreMissionRatioSuspense,
  useCfoSofrSensitivitySuspense,
  useCfoCoSpreadsSuspense,
  useCfoMbsUnrealizedSuspense,
} from "@/lib/api";
import { Panel } from "@/components/common/panel";
import { RowsBoundary } from "@/components/common/rows-view";
import { AiBriefing } from "@/components/common/ai-briefing";
import { AnomalyRadar } from "@/components/common/anomaly-radar";
import { BarChartView, LineChartView, AreaChartView } from "@/components/common/charts";
import { fmtNum } from "@/lib/format";

export const Route = createFileRoute("/cfo")({ component: CfoCockpit });

function SofrControl() {
  const [bps, setBps] = useState(25);
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">Parallel SOFR shift</span>
        <input
          type="range"
          min={-100}
          max={100}
          step={25}
          value={bps}
          onChange={(e) => setBps(Number(e.target.value))}
          className="flex-1 accent-[var(--persona)]"
        />
        <span className="tnum persona-text w-16 text-right text-sm font-semibold">
          {bps > 0 ? "+" : ""}{bps} bps
        </span>
      </div>
      <RowsBoundary
        key={bps}
        hook={useCfoSofrSensitivitySuspense as never}
        options={{ params: { bps } }}
        height="14rem"
        render={(d) => {
          const total = d.rows.reduce((a, r) => a + (Number(r.annual_nii_impact_mm) || 0), 0);
          return (
            <div className="space-y-3">
              <div className="glass rounded-lg p-3">
                <div className="text-xs text-muted-foreground">Estimated annual NII impact</div>
                <div className={`tnum text-2xl font-semibold ${total >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {total >= 0 ? "+" : ""}${fmtNum(total, 2)}M
                </div>
              </div>
              <BarChartView
                data={d.rows}
                x="index_type"
                bars={[{ key: "balance_bn", name: "Balance ($B)" }]}
                height={180}
              />
            </div>
          );
        }}
      />
    </div>
  );
}

function CfoCockpit() {
  return (
    <div className="space-y-5">
      <AiBriefing persona="cfo" title="Treasury briefing" />
      <AnomalyRadar persona="cfo" />
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title="Advances vs Forecast" subtitle="Quarterly actual vs treasury plan" icon={<Landmark className="size-4" />} persona>
          <RowsBoundary
            hook={useCfoAdvancesVsForecastSuspense as never}
            render={(d) => (
              <BarChartView
                data={d.rows}
                x="quarter"
                bars={[
                  { key: "actual_bn", name: "Actual ($B)" },
                  { key: "forecast_bn", name: "Forecast ($B)" },
                ]}
              />
            )}
          />
        </Panel>

        <Panel title="Core Mission Asset Ratio" subtitle="(Advances + AMA) / Consolidated Obligations" icon={<Target className="size-4" />}>
          <RowsBoundary
            hook={useCfoCoreMissionRatioSuspense as never}
            render={(d) => (
              <AreaChartView data={d.rows} x="quarter" areaKey="core_mission_ratio_pct" />
            )}
          />
        </Panel>

        <Panel title="+/- SOFR Rate Sensitivity" subtitle="Interactive NII impact on floating advances" icon={<Waves className="size-4" />} persona>
          <SofrControl />
        </Panel>

        <Panel title="Consolidated Obligation Spreads" subtitle="Spread to Treasury, trailing 90 days" icon={<TrendingUp className="size-4" />}>
          <RowsBoundary
            hook={useCfoCoSpreadsSuspense as never}
            render={(d) => (
              <LineChartView data={d.rows} x="issue_date" lines={[{ key: "spread_to_treasury_bps", name: "bps" }]} />
            )}
          />
        </Panel>

        <Panel title="Unrealized MBS G/L by Vintage" subtitle="Agency MBS mark-to-market" icon={<Layers className="size-4" />} className="lg:col-span-2">
          <RowsBoundary
            hook={useCfoMbsUnrealizedSuspense as never}
            render={(d) => (
              <BarChartView data={d.rows} x="vintage_year" bars={[{ key: "unrealized_mm", name: "Unrealized ($M)" }]} />
            )}
          />
        </Panel>
      </div>

    </div>
  );
}
