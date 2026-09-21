import { genieSpaceForPersona, type PersonaId } from "./personas";

export type AgentReportBlock =
  | { kind: "text"; text: string }
  | {
      kind: "table";
      columns: string[];
      rows: Record<string, unknown>[];
      sql?: string | null;
      total_row_count?: number | null;
    };

export type AgentEvent =
  | { type: "created"; conversation_id?: string | null }
  | { type: "reasoning"; text: string }
  | { type: "query"; id?: string | null; title?: string | null; sql: string }
  | { type: "report"; blocks: AgentReportBlock[] }
  | { type: "done" }
  | { type: "error"; message: string };

export type CitationSource = { n: number; title: string; url: string; sql?: string | null };

/** Map inline citation markers (``[\[n\]](url)`` with ``gra_focus=<query_id>``) back
 * to the queries the agent ran, so we can render a Sources list. */
export function extractSources(
  text: string,
  queries: { id?: string | null; title?: string | null; sql?: string | null }[],
): CitationSource[] {
  const byId = new Map(queries.filter((q) => q.id).map((q) => [q.id as string, q]));
  const link = /\[\\\[(\d+)\\\]\]\((https?:\/\/[^)]+)\)/g;
  const seen = new Map<number, CitationSource>();
  let m: RegExpExecArray | null;
  while ((m = link.exec(text)) !== null) {
    const n = Number(m[1]);
    if (seen.has(n)) continue;
    const url = m[2];
    const focus = /gra_focus=([0-9a-fA-F]+)/.exec(url);
    const q = focus ? byId.get(focus[1]) : undefined;
    seen.set(n, { n, title: q?.title ?? `Supporting query ${n}`, url, sql: q?.sql });
  }
  return [...seen.values()].sort((a, b) => a.n - b.n);
}

/**
 * POST to the Agent mode NDJSON stream and invoke `onEvent` for each event as it
 * arrives. Resolves when the stream ends (or aborts via `signal`).
 */
export async function streamGenieAgent(
  persona: PersonaId,
  question: string,
  conversationId: string | null,
  onEvent: (e: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const space = genieSpaceForPersona(persona);
  let res: Response;
  try {
    res = await fetch(`/api/genie-agent/${space}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, conversation_id: conversationId }),
      signal,
    });
  } catch (e) {
    if ((e as Error).name === "AbortError") return;
    onEvent({ type: "error", message: (e as Error).message });
    return;
  }

  if (!res.ok || !res.body) {
    let msg = `Agent mode request failed (${res.status})`;
    try {
      const j = await res.json();
      msg = j.detail || j.message || msg;
    } catch {
      /* ignore */
    }
    onEvent({ type: "error", message: msg });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, idx).trim();
        buf = buf.slice(idx + 1);
        if (!line) continue;
        try {
          onEvent(JSON.parse(line) as AgentEvent);
        } catch {
          /* skip malformed line */
        }
      }
    }
  } catch (e) {
    if ((e as Error).name !== "AbortError") {
      onEvent({ type: "error", message: (e as Error).message });
    }
    return;
  }

  const tail = buf.trim();
  if (tail) {
    try {
      onEvent(JSON.parse(tail) as AgentEvent);
    } catch {
      /* ignore */
    }
  }
}
