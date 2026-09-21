import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { fmtNum, titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";

type Row = Record<string, unknown>;

function renderCell(key: string, value: unknown) {
  if (value === null || value === undefined) return <span className="text-muted-foreground">-</span>;
  if (typeof value === "boolean") {
    return (
      <Badge variant={value ? "default" : "secondary"} className="text-[10px]">
        {value ? "Yes" : "No"}
      </Badge>
    );
  }
  if (typeof value === "number") {
    return <span className="tnum">{fmtNum(value, Number.isInteger(value) ? 0 : 1)}</span>;
  }
  const s = String(value);
  const lower = key.toLowerCase();
  if (lower === "severity" || lower === "internal_rating") {
    const tone =
      /high|c|d/i.test(s) && s.length <= 6
        ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
        : /medium|bbb|bb/i.test(s)
          ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
          : "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
    return <span className={cn("rounded-md border px-2 py-0.5 text-xs font-medium", tone)}>{s}</span>;
  }
  return <span>{s}</span>;
}

export function RowsTable({
  columns,
  rows,
  numericRight = true,
  maxHeight = "auto",
}: {
  columns: string[];
  rows: Row[];
  numericRight?: boolean;
  maxHeight?: string;
}) {
  if (!rows.length) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No rows.</p>;
  }
  const cols = columns.length ? columns : Object.keys(rows[0]);
  const isNum = (c: string) => rows.some((r) => typeof r[c] === "number");
  return (
    <div className="overflow-auto rounded-lg border border-border/60" style={{ maxHeight }}>
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-card/95 backdrop-blur">
          <TableRow className="hover:bg-transparent">
            {cols.map((c) => (
              <TableHead
                key={c}
                className={cn(
                  "whitespace-nowrap text-[11px] uppercase tracking-wide",
                  numericRight && isNum(c) && "text-right",
                )}
              >
                {titleCase(c)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r, i) => (
            <TableRow key={i} className="border-border/40">
              {cols.map((c) => (
                <TableCell
                  key={c}
                  className={cn(
                    "whitespace-nowrap py-2 text-sm",
                    numericRight && typeof r[c] === "number" && "text-right tnum",
                  )}
                >
                  {renderCell(c, r[c])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
