import { useEffect, useState, type ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  ShieldCheck,
  Landmark,
  Gauge,
  Users,
  HeartHandshake,
  Network,
  Table2,
  Workflow,
  ChevronRight,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { PERSONAS, personaFromPath, type PersonaId } from "@/lib/personas";
import { cn } from "@/lib/utils";
import { FreshnessChip } from "./freshness-chip";
import { GenieDock } from "./genie-dock";
import { ASK_GENIE_EVENT, type AskGenieDetail, type AskGenieMode } from "@/lib/genie-bus";

const GENIE_OPEN_KEY = "fhlb.genie.open";

const ICONS: Record<PersonaId, LucideIcon> = {
  overview: LayoutDashboard,
  cio: ShieldCheck,
  cfo: Landmark,
  cro: Gauge,
  cbo: Users,
  mission: HeartHandshake,
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const active = personaFromPath(pathname);
  const cleanPath = pathname.replace(/\/$/, "");
  const isArch = cleanPath === "/architecture";
  const isData = cleanPath === "/data-model";
  const isEng = cleanPath === "/data-engineering";
  const isSpecial = isArch || isData || isEng;
  const ActiveIcon = ICONS[active.id];
  const headerIcon = isArch ? (
    <Network className="size-5" />
  ) : isData ? (
    <Table2 className="size-5" />
  ) : isEng ? (
    <Workflow className="size-5" />
  ) : (
    <ActiveIcon className="size-5" />
  );
  const headerKicker = isArch ? "Platform" : isData ? "Data" : isEng ? "Pipeline" : active.short;
  const headerTitle = isArch
    ? "Platform Architecture"
    : isData
      ? "Data Model"
      : isEng
        ? "Data Engineering"
        : active.label;
  const headerSubtitle = isArch
    ? "How the app uses the Databricks platform"
    : isData
      ? "Governed tables by business domain"
      : isEng
        ? "Medallion flow & Lakeflow declarative pipeline"
        : active.title;
  const [genieOpen, setGenieOpen] = useState(false);
  const [pendingAsk, setPendingAsk] = useState<{
    question: string;
    mode: AskGenieMode;
    nonce: number;
  } | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setGenieOpen(window.localStorage.getItem(GENIE_OPEN_KEY) === "1");
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(GENIE_OPEN_KEY, genieOpen ? "1" : "0");
  }, [genieOpen]);

  // A suggested follow-up (or any component) can hand a question to the Genie dock.
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<AskGenieDetail>).detail;
      if (!detail?.question) return;
      setGenieOpen(true);
      setPendingAsk({ question: detail.question, mode: detail.mode ?? "standard", nonce: Date.now() });
    };
    window.addEventListener(ASK_GENIE_EVENT, handler);
    return () => window.removeEventListener(ASK_GENIE_EVENT, handler);
  }, []);

  return (
    <div
      className="exec-bg min-h-screen text-foreground"
      style={{ ["--persona" as string]: `oklch(${active.accent})` }}
    >
      <div className="flex">
        {/* Sidebar */}
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border/60 bg-sidebar/60 px-3 py-5 backdrop-blur-xl lg:flex">
          <div className="mb-6 flex items-center gap-2.5 px-2">
            <div className="grid size-9 place-items-center rounded-xl persona-bg-soft persona-text">
              <Landmark className="size-5" />
            </div>
            <div className="leading-tight">
              <div className="text-sm font-semibold">FHLB Des Moines</div>
              <div className="text-[11px] text-muted-foreground">Command Center</div>
            </div>
          </div>

          <nav className="flex flex-col gap-1">
            {PERSONAS.map((p) => {
              const isActive = p.id === active.id && !isSpecial;
              const Icon = ICONS[p.id];
              return (
                <Link
                  key={p.id}
                  to={p.path}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                    isActive
                      ? "persona-bg-soft font-medium text-foreground persona-ring"
                      : "text-muted-foreground hover:bg-accent/40 hover:text-foreground",
                  )}
                  style={isActive ? { ["--persona" as string]: `oklch(${p.accent})` } : undefined}
                >
                  <span className={isActive ? "persona-text" : ""}>
                    <Icon className="size-4" />
                  </span>
                  <span className="flex-1">{p.short}</span>
                  {isActive && <span className="size-1.5 rounded-full bg-[var(--persona)]" />}
                </Link>
              );
            })}

            <div className="my-2 border-t border-border/50" />
            <Link
              to="/architecture"
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                isArch
                  ? "persona-bg-soft font-medium text-foreground persona-ring"
                  : "text-muted-foreground hover:bg-accent/40 hover:text-foreground",
              )}
            >
              <span className={isArch ? "persona-text" : ""}>
                <Network className="size-4" />
              </span>
              <span className="flex-1">Architecture</span>
              {isArch && <span className="size-1.5 rounded-full bg-[var(--persona)]" />}
            </Link>
            <Link
              to="/data-model"
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                isData
                  ? "persona-bg-soft font-medium text-foreground persona-ring"
                  : "text-muted-foreground hover:bg-accent/40 hover:text-foreground",
              )}
            >
              <span className={isData ? "persona-text" : ""}>
                <Table2 className="size-4" />
              </span>
              <span className="flex-1">Data Model</span>
              {isData && <span className="size-1.5 rounded-full bg-[var(--persona)]" />}
            </Link>
            <Link
              to="/data-engineering"
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                isEng
                  ? "persona-bg-soft font-medium text-foreground persona-ring"
                  : "text-muted-foreground hover:bg-accent/40 hover:text-foreground",
              )}
            >
              <span className={isEng ? "persona-text" : ""}>
                <Workflow className="size-4" />
              </span>
              <span className="flex-1">Data Engineering</span>
              {isEng && <span className="size-1.5 rounded-full bg-[var(--persona)]" />}
            </Link>
          </nav>

          <div className="mt-auto rounded-lg border border-border/50 bg-card/40 p-3 text-[11px] text-muted-foreground">
            <div className="mb-1 flex items-center gap-1.5 font-medium text-foreground/80">
              <ShieldCheck className="size-3.5 text-emerald-400" /> Full platform, live
            </div>
            Lakehouse · Genie · AI Gateway · Lakebase
          </div>
        </aside>

        {/* Main */}
        <div className="flex min-h-screen flex-1 flex-col">
          <header className="exec-header sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-border/40 px-5 py-3.5 backdrop-blur-xl">
            <div
              key={isArch ? "arch" : isData ? "data" : isEng ? "eng" : active.id}
              className="animate-fade-up flex min-w-0 items-center gap-3"
            >
              <div className="persona-bg-soft persona-text persona-ring grid size-10 shrink-0 place-items-center rounded-xl">
                {headerIcon}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em]">
                  <span className="persona-text">FHLB Des Moines</span>
                  <ChevronRight className="size-3 text-muted-foreground/60" />
                  <span className="text-muted-foreground">{headerKicker}</span>
                </div>
                <h1 className="gradient-text truncate text-xl font-semibold leading-tight tracking-tight">
                  {headerTitle}
                </h1>
                <p className="truncate text-xs text-muted-foreground">
                  {headerSubtitle}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2.5">
              <OwnerPill label={isSpecial ? "Live demo" : active.exec} />
              <span className="glass hidden items-center gap-1.5 rounded-full px-3 py-1.5 text-xs sm:inline-flex">
                <span className="live-dot size-2 rounded-full bg-[var(--persona)]" />
                <span className="text-muted-foreground">Live</span>
              </span>
              <FreshnessChip />
            </div>
            <span className="header-accent" />
          </header>

          {/* Mobile nav */}
          <div className="flex gap-1 overflow-x-auto border-b border-border/60 px-3 py-2 lg:hidden">
            {PERSONAS.map((p) => {
              const isActive = p.id === active.id && !isSpecial;
              return (
                <Link
                  key={p.id}
                  to={p.path}
                  className={cn(
                    "whitespace-nowrap rounded-full px-3 py-1 text-xs",
                    isActive ? "persona-bg-soft persona-text font-medium" : "text-muted-foreground",
                  )}
                  style={{ ["--persona" as string]: `oklch(${p.accent})` }}
                >
                  {p.short}
                </Link>
              );
            })}
            <Link
              to="/architecture"
              className={cn(
                "flex items-center gap-1 whitespace-nowrap rounded-full px-3 py-1 text-xs",
                isArch ? "persona-bg-soft persona-text font-medium" : "text-muted-foreground",
              )}
            >
              <Network className="size-3" /> Architecture
            </Link>
            <Link
              to="/data-model"
              className={cn(
                "flex items-center gap-1 whitespace-nowrap rounded-full px-3 py-1 text-xs",
                isData ? "persona-bg-soft persona-text font-medium" : "text-muted-foreground",
              )}
            >
              <Table2 className="size-3" /> Data Model
            </Link>
            <Link
              to="/data-engineering"
              className={cn(
                "flex items-center gap-1 whitespace-nowrap rounded-full px-3 py-1 text-xs",
                isEng ? "persona-bg-soft persona-text font-medium" : "text-muted-foreground",
              )}
            >
              <Workflow className="size-3" /> Data Engineering
            </Link>
          </div>

          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-5 sm:px-6">{children}</main>
        </div>
      </div>

      <GenieDock
        persona={active.id}
        open={genieOpen}
        onOpenChange={setGenieOpen}
        pendingAsk={pendingAsk}
      />
    </div>
  );
}

/** Executive owner chip. `label` is either "Name - ROLE" (a person) or a plain
 * label like "Board & CEO" for shared views, in which case we drop the initials. */
function OwnerPill({ label }: { label: string }) {
  const [name, role] = label.split(" - ");
  const initials = role
    ? name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((w) => w[0]!)
        .join("")
        .toUpperCase()
    : null;

  return (
    <div className="glass hidden items-center gap-2 rounded-full py-1 pl-1 pr-3 md:flex">
      <span className="persona-bg-soft persona-text grid size-6 shrink-0 place-items-center rounded-full text-[10px] font-semibold">
        {initials ?? <UserRound className="size-3.5" />}
      </span>
      <div className="leading-tight">
        <div className="text-xs font-medium text-foreground/90">{name}</div>
        {role && (
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{role}</div>
        )}
      </div>
    </div>
  );
}
