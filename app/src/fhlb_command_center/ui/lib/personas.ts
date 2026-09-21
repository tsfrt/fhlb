export type PersonaId = "overview" | "cio" | "cfo" | "cro" | "cbo" | "mission";

export interface Persona {
  id: PersonaId;
  path: string;
  label: string;
  short: string;
  exec: string;
  title: string;
  accent: string; // oklch triplet for --persona
  blurb: string;
}

export const PERSONAS: Persona[] = [
  {
    id: "overview",
    path: "/",
    label: "Executive Overview",
    short: "Overview",
    exec: "Board & CEO",
    title: "The whole Bank, as of this morning",
    accent: "0.72 0.14 233",
    blurb: "Cross-persona command view",
  },
  {
    id: "cio",
    path: "/cio",
    label: "Data Governance & Operations",
    short: "CIO",
    exec: "Kevin Larkin - CIO",
    title: "Governed data, ready for the examiner",
    accent: "0.68 0.19 300",
    blurb: "FHFA readiness, lineage, dual-run",
  },
  {
    id: "cfo",
    path: "/cfo",
    label: "Finance & Treasury",
    short: "CFO",
    exec: "James Livingston - CFO",
    title: "Balance sheet & mission on one screen",
    accent: "0.74 0.13 205",
    blurb: "Advances, ratio, rate sensitivity",
  },
  {
    id: "cro",
    path: "/cro",
    label: "Credit & Collateral",
    short: "CRO",
    exec: "Joelyn Jensen-Marren - CRO",
    title: "Where credit risk is concentrating",
    accent: "0.66 0.22 20",
    blurb: "Ratings, collateral, concentration",
  },
  {
    id: "cbo",
    path: "/cbo",
    label: "Member & Products",
    short: "CBO",
    exec: "Wil Osborn - CBO",
    title: "Grow the wallet with every member",
    accent: "0.8 0.16 85",
    blurb: "Utilization, whitespace, prospects",
  },
  {
    id: "mission",
    path: "/mission",
    label: "Mission & Affordable Housing",
    short: "Mission",
    exec: "Community Investment",
    title: "The $200M pledge, in motion",
    accent: "0.75 0.15 155",
    blurb: "Pledge, AHP, governed assistant",
  },
];

export const PERSONA_MAP: Record<string, Persona> = Object.fromEntries(
  PERSONAS.map((p) => [p.id, p]),
);

export function personaFromPath(pathname: string): Persona {
  const clean = pathname.replace(/\/$/, "");
  const match = PERSONAS.find((p) => p.path !== "/" && clean.startsWith(p.path));
  return match ?? PERSONAS[0];
}

/** Persona ids that map to a dedicated Genie space. Overview has none, so it
 * borrows the broad, balance-sheet-oriented CFO space. */
export type GenieSpacePersona = Exclude<PersonaId, "overview">;

export function genieSpaceForPersona(id: PersonaId): GenieSpacePersona {
  return id === "overview" ? "cfo" : id;
}
