import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "@/lib/format";

const axisProps = {
  tick: { fontSize: 11, fill: "var(--color-muted-foreground)" },
  tickLine: false,
  axisLine: { stroke: "var(--color-border)" },
} as const;

const tooltipStyle = {
  contentStyle: {
    background: "var(--color-popover)",
    border: "1px solid var(--color-border)",
    borderRadius: 10,
    fontSize: 12,
    color: "var(--color-popover-foreground)",
  },
  labelStyle: { color: "var(--color-muted-foreground)", fontSize: 11 },
  cursor: { fill: "color-mix(in oklch, var(--persona) 12%, transparent)" },
} as const;

type Datum = Record<string, unknown>;

export function BarChartView({
  data,
  x,
  bars,
  height = 240,
  stacked = false,
}: {
  data: Datum[];
  x: string;
  bars: { key: string; name?: string; color?: string }[];
  height?: number;
  stacked?: boolean;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey={x} {...axisProps} interval="preserveStartEnd" />
        <YAxis {...axisProps} width={44} />
        <Tooltip {...tooltipStyle} />
        {bars.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
        {bars.map((b, i) => (
          <Bar
            key={b.key}
            dataKey={b.key}
            name={b.name ?? b.key}
            stackId={stacked ? "a" : undefined}
            fill={b.color ?? CHART_COLORS[i % CHART_COLORS.length]}
            radius={stacked ? 0 : [4, 4, 0, 0]}
            maxBarSize={48}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function LineChartView({
  data,
  x,
  lines,
  height = 240,
}: {
  data: Datum[];
  x: string;
  lines: { key: string; name?: string; color?: string }[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey={x} {...axisProps} interval="preserveStartEnd" />
        <YAxis {...axisProps} width={44} />
        <Tooltip {...tooltipStyle} cursor={{ stroke: "var(--persona)", strokeWidth: 1 }} />
        {lines.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
        {lines.map((l, i) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.name ?? l.key}
            stroke={l.color ?? CHART_COLORS[i % CHART_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function AreaChartView({
  data,
  x,
  areaKey,
  color = "var(--persona)",
  height = 220,
}: {
  data: Datum[];
  x: string;
  areaKey: string;
  color?: string;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
        <defs>
          <linearGradient id={`grad-${areaKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.5} />
            <stop offset="95%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey={x} {...axisProps} interval="preserveStartEnd" />
        <YAxis {...axisProps} width={44} />
        <Tooltip {...tooltipStyle} />
        <Area
          type="monotone"
          dataKey={areaKey}
          stroke={color}
          strokeWidth={2}
          fill={`url(#grad-${areaKey})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function DonutChartView({
  data,
  nameKey,
  valueKey,
  height = 240,
}: {
  data: Datum[];
  nameKey: string;
  valueKey: string;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Tooltip {...tooltipStyle} />
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={nameKey}
          innerRadius="55%"
          outerRadius="82%"
          paddingAngle={2}
          stroke="var(--color-card)"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
