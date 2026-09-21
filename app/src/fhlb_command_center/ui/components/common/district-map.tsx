import { useMemo, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { scaleLinear } from "d3-scale";
import {
  DISTRICT_STATES,
  PACIFIC_TERRITORIES,
  STATE_NAME_TO_ABBR,
  US_TOPO_JSON,
} from "@/lib/fhlb-states";
import { fmtNum } from "@/lib/format";

interface DistrictRow {
  state: string;
  members: number;
  advances_bn: number;
}

export function DistrictMap({ rows }: { rows: DistrictRow[] }) {
  const byState = useMemo(() => {
    const m: Record<string, DistrictRow> = {};
    for (const r of rows) m[r.state] = r;
    return m;
  }, [rows]);

  const max = useMemo(
    () => Math.max(1, ...rows.map((r) => r.advances_bn || 0)),
    [rows],
  );
  const color = scaleLinear<string>()
    .domain([0, max])
    .range(["color-mix(in oklch, var(--persona) 12%, var(--card))", "var(--persona)"]);

  const [hover, setHover] = useState<{ name: string; row?: DistrictRow } | null>(null);

  return (
    <div className="relative">
      <ComposableMap
        projection="geoAlbersUsa"
        projectionConfig={{ scale: 900 }}
        style={{ width: "100%", height: "auto" }}
      >
        <Geographies geography={US_TOPO_JSON}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const name = geo.properties.name as string;
              const abbr = STATE_NAME_TO_ABBR[name];
              const inDistrict = abbr && DISTRICT_STATES.includes(abbr);
              const row = abbr ? byState[abbr] : undefined;
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onMouseEnter={() => inDistrict && setHover({ name, row })}
                  onMouseLeave={() => setHover(null)}
                  style={{
                    default: {
                      fill: inDistrict ? color(row?.advances_bn ?? 0) : "var(--color-muted)",
                      stroke: "var(--color-background)",
                      strokeWidth: 0.5,
                      outline: "none",
                      opacity: inDistrict ? 1 : 0.25,
                    },
                    hover: {
                      fill: inDistrict ? "var(--persona)" : "var(--color-muted)",
                      outline: "none",
                      cursor: inDistrict ? "pointer" : "default",
                    },
                    pressed: { outline: "none" },
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      {hover?.row && (
        <div className="glass pointer-events-none absolute left-3 top-3 rounded-lg px-3 py-2 text-xs">
          <div className="font-semibold">{hover.name}</div>
          <div className="text-muted-foreground">
            {fmtNum(hover.row.members, 0)} members · ${fmtNum(hover.row.advances_bn, 2)}B advances
          </div>
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
        <div className="flex items-center gap-2">
          <span>Advances</span>
          <span className="h-2 w-24 rounded-full" style={{ background: "linear-gradient(90deg, color-mix(in oklch, var(--persona) 12%, var(--card)), var(--persona))" }} />
          <span>${fmtNum(max, 1)}B</span>
        </div>
        <div>+ Pacific territories: {PACIFIC_TERRITORIES.join(", ")}</div>
      </div>
    </div>
  );
}
