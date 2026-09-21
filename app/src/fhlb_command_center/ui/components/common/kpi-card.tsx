import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface KpiProps {
  label: string;
  value: string;
  sublabel?: string;
  icon?: ReactNode;
  tone?: "default" | "good" | "warn" | "bad";
  delay?: number;
}

const toneClass: Record<NonNullable<KpiProps["tone"]>, string> = {
  default: "text-foreground",
  good: "text-emerald-400",
  warn: "text-amber-400",
  bad: "text-rose-400",
};

export function KpiCard({ label, value, sublabel, icon, tone = "default", delay = 0 }: KpiProps) {
  return (
    <div
      className="glass animate-fade-up relative overflow-hidden rounded-xl p-4"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="exec-grid absolute inset-0 opacity-40" />
      <div className="relative flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        {icon && <span className="persona-text opacity-80">{icon}</span>}
      </div>
      <div className={cn("relative mt-2 text-3xl font-semibold tnum tracking-tight", toneClass[tone])}>
        {value}
      </div>
      {sublabel && <div className="relative mt-1 text-xs text-muted-foreground">{sublabel}</div>}
    </div>
  );
}
