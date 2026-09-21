import type { PersonaId } from "@/lib/personas";
import { ChatPanel } from "./chat-panel";

/**
 * Inline, in-cockpit Genie chat. Backed by the full multi-turn ChatPanel and
 * scoped to the section's persona Genie space.
 */
export function GenieBox({
  persona,
  suggestions = [],
}: {
  persona: PersonaId;
  suggestions?: string[];
}) {
  return (
    <ChatPanel
      persona={persona}
      suggestions={suggestions}
      className="max-h-[520px]"
    />
  );
}
