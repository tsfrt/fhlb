import { Sparkles, ChevronRight } from "lucide-react";
import {
  PERSONA_MAP,
  genieSpaceForPersona,
  type PersonaId,
} from "@/lib/personas";
import { cn } from "@/lib/utils";
import { ChatPanel } from "@/components/common/chat-panel";

const SUGGESTIONS: Record<string, string[]> = {
  cfo: [
    "What is total advances outstanding right now?",
    "Show the core mission asset ratio trend by quarter",
    "How have consolidated obligation spreads moved over the last 90 days?",
  ],
  cro: [
    "Which members are past the AB 2024-03 rating cadence, ranked by advances?",
    "Where is our collateral OC cushion thinning the most?",
    "Show MPF delinquency trends over the last year",
  ],
  cbo: [
    "Which members have the largest unused borrowing capacity?",
    "Show advance utilization by member type and state",
    "Which members use only one product?",
  ],
  cio: [
    "How many open FHFA data quality exceptions do we have?",
    "Show dual-run cost of SQL Server versus Fabric",
    "What is the model validation backlog?",
  ],
  mission: [
    "How much of the $200M pledge have we deployed year to date?",
    "Show AHP units by income tier",
    "What is subsidy per unit efficiency by program?",
  ],
};

export function GenieDock({
  persona,
  open,
  onOpenChange,
  pendingAsk,
}: {
  persona: PersonaId;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  pendingAsk?: { question: string; mode?: "standard" | "agent"; nonce: number } | null;
}) {
  const space = genieSpaceForPersona(persona);
  const spaceLabel = PERSONA_MAP[space]?.short ?? space.toUpperCase();
  const accent = PERSONA_MAP[space]?.accent;

  return (
    <>
      {/* Collapsed edge tab */}
      <button
        onClick={() => onOpenChange(true)}
        aria-label="Open Genie chat"
        className={cn(
          "group fixed right-0 top-1/2 z-30 flex -translate-y-1/2 items-center gap-2 rounded-l-xl border border-r-0 border-border/60 bg-card/80 py-4 pl-3 pr-2.5 backdrop-blur-xl transition",
          "persona-ring hover:pr-3.5",
          open && "pointer-events-none translate-x-full opacity-0",
        )}
        style={{ ["--persona" as string]: accent ? `oklch(${accent})` : undefined }}
      >
        <span className="persona-text">
          <Sparkles className="size-4" />
        </span>
        <span
          className="text-xs font-medium tracking-wide text-foreground/80 group-hover:text-foreground"
          style={{ writingMode: "vertical-rl" }}
        >
          Ask Genie
        </span>
      </button>

      {/* Docked chat panel */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-40 flex h-screen w-full flex-col border-l border-border/60 bg-sidebar/80 backdrop-blur-2xl transition-transform duration-300 ease-out sm:w-[440px]",
          open ? "translate-x-0" : "pointer-events-none translate-x-full",
        )}
        style={{ ["--persona" as string]: accent ? `oklch(${accent})` : undefined }}
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between gap-3 border-b border-border/60 px-4 py-3.5">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="persona-bg-soft persona-text grid size-9 shrink-0 place-items-center rounded-xl">
              <Sparkles className="size-4" />
            </div>
            <div className="min-w-0 leading-tight">
              <div className="truncate text-sm font-semibold">{spaceLabel} Genie space</div>
              <div className="truncate text-[11px] text-muted-foreground">
                Natural-language analytics · live lakehouse
              </div>
            </div>
          </div>
          <button
            onClick={() => onOpenChange(false)}
            aria-label="Collapse Genie chat"
            className="grid size-8 shrink-0 place-items-center rounded-lg text-muted-foreground transition hover:bg-accent/40 hover:text-foreground"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>

        <div className="min-h-0 flex-1 px-4 py-4">
          {open && (
            <ChatPanel
              key={space}
              persona={persona}
              suggestions={SUGGESTIONS[space] ?? []}
              className="h-full"
              pendingAsk={pendingAsk}
            />
          )}
        </div>
      </aside>
    </>
  );
}
