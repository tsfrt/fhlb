import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  Sparkles,
  Telescope,
  CornerDownLeft,
  Database,
  Loader2,
  RotateCcw,
  ChevronDown,
} from "lucide-react";
import { useGenieAsk, type GenieResponse } from "@/lib/api";
import {
  streamGenieAgent,
  type AgentEvent,
  type AgentReportBlock,
} from "@/lib/genie-agent";
import { genieSpaceForPersona, type PersonaId } from "@/lib/personas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { GenieResult } from "./genie-result";
import { Markdown } from "./markdown";

type ChatMode = "standard" | "agent";

type AgentStep =
  | { kind: "reasoning"; text: string }
  | { kind: "query"; title?: string | null; sql: string };

type ChatMessage = {
  id: string;
  role: "user" | "genie";
  mode: ChatMode;
  content: string;
  sql?: string | null;
  columns?: string[];
  rows?: Record<string, unknown>[];
  vizUrl?: string | null;
  vizTitle?: string | null;
  steps?: AgentStep[];
  blocks?: AgentReportBlock[];
  status: "pending" | "streaming" | "done" | "error";
};

let _seq = 0;
const nextId = () => `m${Date.now()}_${_seq++}`;

function StandardMessage({ msg }: { msg: ChatMessage }) {
  const rows = msg.rows ?? [];
  return (
    <div className="w-full max-w-[96%] space-y-2">
      <div
        className={cn(
          "glass rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed",
          msg.status === "error" && "border-destructive/40 text-destructive",
        )}
      >
        {msg.status === "error" ? msg.content : <Markdown>{msg.content}</Markdown>}
      </div>
      {(rows.length > 0 || msg.vizUrl) && (
        <GenieResult
          columns={msg.columns ?? []}
          rows={rows}
          sql={msg.sql}
          vizUrl={msg.vizUrl}
          vizTitle={msg.vizTitle}
        />
      )}
    </div>
  );
}

function AgentMessage({ msg }: { msg: ChatMessage }) {
  const steps = msg.steps ?? [];
  const busy = msg.status === "pending" || msg.status === "streaming";
  const [showSteps, setShowSteps] = useState(true);
  // Once the report is in, collapse the work log by default.
  useEffect(() => {
    if (msg.status === "done") setShowSteps(false);
  }, [msg.status]);

  return (
    <div className="w-full max-w-[96%] space-y-2.5">
      <div className="persona-text flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide">
        <Telescope className="size-3.5" /> Deep research
        {busy && <Loader2 className="size-3 animate-spin" />}
      </div>

      {steps.length > 0 && (
        <div className="glass rounded-xl">
          <button
            onClick={() => setShowSteps((v) => !v)}
            className="flex w-full items-center justify-between gap-2 px-3 py-2 text-xs text-muted-foreground transition hover:text-foreground"
          >
            <span>
              {busy ? "Researching" : "Analysis"} · {steps.length} step
              {steps.length === 1 ? "" : "s"}
            </span>
            <ChevronDown
              className={cn("size-4 transition-transform", showSteps && "rotate-180")}
            />
          </button>
          {showSteps && (
            <div className="space-y-2.5 border-t border-border/50 px-3 py-2.5">
              {steps.map((s, i) =>
                s.kind === "reasoning" ? (
                  <div key={i} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                    <Sparkles className="persona-text mt-0.5 size-3 shrink-0" />
                    <span>{s.text}</span>
                  </div>
                ) : (
                  <QueryStep key={i} title={s.title} sql={s.sql} />
                ),
              )}
            </div>
          )}
        </div>
      )}

      {busy && steps.length === 0 && (
        <div className="glass flex items-center gap-2 rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm text-muted-foreground">
          <Loader2 className="persona-text size-4 animate-spin" />
          Planning the research…
        </div>
      )}

      {msg.status === "error" && (
        <div className="glass rounded-2xl rounded-tl-sm border-destructive/40 px-3.5 py-2.5 text-sm text-destructive">
          {msg.content}
        </div>
      )}

      {(msg.blocks ?? []).map((b, i) =>
        b.kind === "text" ? (
          <div
            key={i}
            className="glass rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm leading-relaxed"
          >
            <Markdown>{b.text}</Markdown>
          </div>
        ) : (
          <div key={i} className="space-y-1.5">
            <GenieResult columns={b.columns} rows={b.rows} sql={b.sql} />
            {typeof b.total_row_count === "number" && b.total_row_count > b.rows.length && (
              <div className="text-[11px] text-muted-foreground">
                Showing {b.rows.length} of {b.total_row_count.toLocaleString()} rows
              </div>
            )}
          </div>
        ),
      )}
    </div>
  );
}

function QueryStep({ title, sql }: { title?: string | null; sql: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-1.5 text-xs font-medium text-foreground/80 transition hover:text-foreground"
      >
        <Database className="persona-text size-3 shrink-0" />
        <span className="truncate text-left">{title || "SQL query"}</span>
        {sql && (
          <ChevronDown
            className={cn(
              "ml-auto size-3.5 shrink-0 text-muted-foreground transition-transform",
              open && "rotate-180",
            )}
          />
        )}
      </button>
      {open && sql && (
        <pre className="overflow-auto rounded-md border border-border/60 bg-background/60 p-2 text-[10.5px] leading-relaxed text-muted-foreground">
          {sql.trim()}
        </pre>
      )}
    </div>
  );
}

function GenieMessage({ msg }: { msg: ChatMessage }) {
  return (
    <div className="animate-fade-up flex flex-col items-start gap-2">
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
        <Sparkles className="persona-text size-3.5" /> Genie
      </div>
      {msg.status === "pending" && msg.mode === "standard" ? (
        <div className="glass flex items-center gap-2 rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-sm text-muted-foreground">
          <Loader2 className="persona-text size-4 animate-spin" />
          Querying the lakehouse…
        </div>
      ) : msg.mode === "agent" ? (
        <AgentMessage msg={msg} />
      ) : (
        <StandardMessage msg={msg} />
      )}
    </div>
  );
}

export function ChatPanel({
  persona,
  suggestions = [],
  className,
  pendingAsk,
}: {
  persona: PersonaId;
  suggestions?: string[];
  className?: string;
  pendingAsk?: { question: string; mode?: ChatMode; nonce: number } | null;
}) {
  const space = useMemo(() => genieSpaceForPersona(persona), [persona]);
  const [q, setQ] = useState("");
  const [mode, setMode] = useState<ChatMode>("standard");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [agentBusy, setAgentBusy] = useState(false);
  const { mutate, isPending } = useGenieAsk();

  const stdConv = useRef<string | null>(null);
  const agentConv = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const handledAsk = useRef<number | null>(null);

  const busy = isPending || agentBusy;

  // Switching persona/section switches Genie space -> start fresh.
  useEffect(() => {
    setMessages([]);
    setQ("");
    stdConv.current = null;
    agentConv.current = null;
    abortRef.current?.abort();
  }, [space]);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const patch = (id: string, fn: (m: ChatMessage) => ChatMessage) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? fn(m) : m)));

  const askStandard = (text: string) => {
    const pendingId = nextId();
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: "user", mode: "standard", content: text, status: "done" },
      { id: pendingId, role: "genie", mode: "standard", content: "", status: "pending" },
    ]);
    mutate(
      { params: { persona: space }, data: { question: text, conversation_id: stdConv.current } },
      {
        onSuccess: (res) => {
          const r: GenieResponse = res.data;
          stdConv.current = r.conversation_id ?? stdConv.current;
          const viz = r.viz;
          const vizUrl =
            viz && r.conversation_id && viz.message_id && viz.attachment_id
              ? `/api/genie-viz/${space}/${r.conversation_id}/${viz.message_id}/${viz.attachment_id}`
              : null;
          patch(pendingId, (m) => ({
            ...m,
            status: "done",
            content: r.answer,
            sql: r.sql,
            columns: r.columns ?? [],
            rows: r.rows ?? [],
            vizUrl,
            vizTitle: viz?.title ?? null,
          }));
        },
        onError: (err) =>
          patch(pendingId, (m) => ({
            ...m,
            status: "error",
            content: `Genie could not answer that: ${err.message}`,
          })),
      },
    );
  };

  const askAgent = (text: string) => {
    const pendingId = nextId();
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: "user", mode: "agent", content: text, status: "done" },
      { id: pendingId, role: "genie", mode: "agent", content: "", steps: [], blocks: [], status: "pending" },
    ]);
    setAgentBusy(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    const onEvent = (e: AgentEvent) => {
      if (e.type === "created") {
        agentConv.current = e.conversation_id ?? agentConv.current;
      } else if (e.type === "reasoning") {
        patch(pendingId, (m) => ({
          ...m,
          status: "streaming",
          steps: [...(m.steps ?? []), { kind: "reasoning", text: e.text }],
        }));
      } else if (e.type === "query") {
        patch(pendingId, (m) => ({
          ...m,
          status: "streaming",
          steps: [...(m.steps ?? []), { kind: "query", title: e.title, sql: e.sql }],
        }));
      } else if (e.type === "report") {
        patch(pendingId, (m) => ({ ...m, status: "done", blocks: e.blocks }));
      } else if (e.type === "error") {
        patch(pendingId, (m) => ({ ...m, status: "error", content: e.message }));
      }
    };

    streamGenieAgent(space, text, agentConv.current, onEvent, ctrl.signal)
      .catch((err) =>
        patch(pendingId, (m) =>
          m.status === "done" ? m : { ...m, status: "error", content: String(err) },
        ),
      )
      .finally(() => {
        setAgentBusy(false);
        patch(pendingId, (m) => (m.status === "streaming" || m.status === "pending" ? { ...m, status: "done" } : m));
      });
  };

  const ask = (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    setQ("");
    if (mode === "agent") askAgent(text);
    else askStandard(text);
  };

  // Auto-ask a question handed off from elsewhere (e.g. a briefing follow-up chip,
  // or an "Investigate" link on an anomaly finding, which requests Agent mode).
  useEffect(() => {
    if (!pendingAsk || pendingAsk.nonce === handledAsk.current || busy) return;
    const text = pendingAsk.question.trim();
    if (!text) return;
    handledAsk.current = pendingAsk.nonce;
    const askMode = pendingAsk.mode ?? "standard";
    setMode(askMode);
    if (askMode === "agent") askAgent(text);
    else askStandard(text);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingAsk?.nonce]);

  const reset = () => {
    abortRef.current?.abort();
    setMessages([]);
    setQ("");
    setAgentBusy(false);
    stdConv.current = null;
    agentConv.current = null;
  };

  const hasChat = messages.length > 0;

  return (
    <div className={cn("flex min-h-0 flex-col", className)}>
      <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        {!hasChat ? (
          <div className="space-y-4 py-2">
            <div className="glass flex items-start gap-3 rounded-2xl p-4">
              <div className="persona-bg-soft persona-text grid size-8 shrink-0 place-items-center rounded-xl">
                {mode === "agent" ? <Telescope className="size-4" /> : <Sparkles className="size-4" />}
              </div>
              <div className="text-sm leading-relaxed text-muted-foreground">
                {mode === "agent" ? (
                  <>
                    <span className="font-medium text-foreground">Agent mode</span> runs
                    multi-step research: it plans, runs several SQL queries, and returns a
                    cited report. Best for open-ended, complex questions.
                  </>
                ) : (
                  <>
                    Ask about this data in plain English. Genie writes the SQL, runs it on
                    the lakehouse, and keeps context across follow-ups. Switch to{" "}
                    <span className="font-medium text-foreground">Agent mode</span> for
                    deeper, multi-step questions.
                  </>
                )}
              </div>
            </div>
            {suggestions.length > 0 && (
              <div className="space-y-2">
                <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Try asking
                </div>
                <div className="flex flex-col gap-2">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => ask(s)}
                      className="persona-bg-soft rounded-xl px-3 py-2 text-left text-sm text-foreground/85 transition hover:text-foreground persona-ring"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="flex justify-end">
                <div className="persona-bg-soft max-w-[85%] rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-sm leading-relaxed text-foreground">
                  {m.content}
                </div>
              </div>
            ) : (
              <GenieMessage key={m.id} msg={m} />
            ),
          )
        )}
      </div>

      {/* Mode switch */}
      <div className="mt-3 flex items-center gap-1.5 rounded-xl border border-border/60 bg-background/40 p-1">
        <ModeButton active={mode === "standard"} onClick={() => setMode("standard")} disabled={busy}>
          <Sparkles className="size-3.5" /> Standard
        </ModeButton>
        <ModeButton active={mode === "agent"} onClick={() => setMode("agent")} disabled={busy}>
          <Telescope className="size-3.5" /> Agent
        </ModeButton>
        <span className="ml-auto pr-1.5 text-[10.5px] text-muted-foreground">
          {mode === "agent" ? "Deep research · slower" : "Fast single-query"}
        </span>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(q);
        }}
        className="mt-2 flex items-center gap-2"
      >
        {hasChat && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={reset}
            title="New conversation"
            className="shrink-0 text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="size-4" />
          </Button>
        )}
        <div className="relative flex-1">
          {mode === "agent" ? (
            <Telescope className="persona-text absolute left-3 top-1/2 size-4 -translate-y-1/2" />
          ) : (
            <Sparkles className="persona-text absolute left-3 top-1/2 size-4 -translate-y-1/2" />
          )}
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={
              mode === "agent"
                ? "Ask a complex, multi-step question…"
                : hasChat
                  ? "Ask a follow-up…"
                  : "Ask Genie about this data…"
            }
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={busy || !q.trim()} className="shrink-0 gap-1.5">
          {busy ? <Loader2 className="size-4 animate-spin" /> : <CornerDownLeft className="size-4" />}
          Ask
        </Button>
      </form>
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  disabled,
  children,
}: {
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex flex-1 items-center justify-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition disabled:opacity-50",
        active
          ? "persona-bg-soft persona-text persona-ring"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}
