/** Lightweight event bus to hand a question off to the docked Genie chat from
 * anywhere in the app (e.g. a suggested follow-up chip in the morning briefing,
 * or an "Investigate" link on an anomaly finding). */

export const ASK_GENIE_EVENT = "fhlb:ask-genie";

export type AskGenieMode = "standard" | "agent";

export type AskGenieDetail = { question: string; mode?: AskGenieMode };

export function askGenie(question: string, mode: AskGenieMode = "standard") {
  window.dispatchEvent(
    new CustomEvent<AskGenieDetail>(ASK_GENIE_EVENT, { detail: { question, mode } }),
  );
}
