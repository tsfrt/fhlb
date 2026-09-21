import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import {
  Users,
  Landmark,
  Boxes,
  Gauge,
  Home,
  TrendingUp,
  PiggyBank,
  HeartHandshake,
  MousePointerClick,
  ShieldCheck,
  Database,
  KeyRound,
  Link2,
  Layers,
} from "lucide-react";

export const Route = createFileRoute("/data-model")({ component: DataModelView });

const BLUE = "0.72 0.14 233";

type Table = {
  name: string;
  grain: string;
  desc: string;
  pk: string;
  fks?: string[];
};

type Domain = {
  id: string;
  name: string;
  accent: string;
  icon: ReactNode;
  blurb: string;
  tables: Table[];
};

const DOMAINS: Domain[] = [
  {
    id: "members",
    name: "Members & Prospects",
    accent: "0.72 0.14 233",
    icon: <Users className="size-5" />,
    blurb: "The institutions we serve and the in-district book we can still win.",
    tables: [
      {
        name: "members",
        grain: "1 row / member",
        desc: "Member institutions — the spine every domain joins back to.",
        pk: "member_id",
      },
      {
        name: "eligible_nonmembers",
        grain: "1 row / prospect",
        desc: "Eligible in-district institutions not yet members.",
        pk: "prospect_id",
      },
    ],
  },
  {
    id: "advances",
    name: "Advances & Pricing",
    accent: "0.74 0.13 205",
    icon: <Landmark className="size-5" />,
    blurb: "Core mission asset — daily positions, pricing, and forecast.",
    tables: [
      {
        name: "advance_daily_balances",
        grain: "member × ~3 days",
        desc: "Daily advance positions over 18 months (largest table).",
        pk: "advance_id",
        fks: ["member_id → members"],
      },
      {
        name: "advance_pricing_daily",
        grain: "maturity × week",
        desc: "Advance pricing vs member funding alternatives.",
        pk: "price_id",
      },
      {
        name: "advance_forecast_quarterly",
        grain: "segment × quarter",
        desc: "Quarterly advance forecast by member segment.",
        pk: "quarter_end_date",
      },
      {
        name: "letters_of_credit",
        grain: "1 row / LoC",
        desc: "Standby letters of credit issued to members by purpose.",
        pk: "loc_id",
        fks: ["member_id → members"],
      },
    ],
  },
  {
    id: "collateral",
    name: "Collateral",
    accent: "0.66 0.22 20",
    icon: <Boxes className="size-5" />,
    blurb: "Lendable value behind every advance, and how it verifies.",
    tables: [
      {
        name: "pledged_collateral",
        grain: "1 row / lot",
        desc: "Pledged lots with lendable value and haircut.",
        pk: "lot_id",
        fks: ["member_id → members"],
      },
      {
        name: "collateral_reviews",
        grain: "type × month",
        desc: "Verification review results and exception rates.",
        pk: "review_id",
      },
    ],
  },
  {
    id: "credit",
    name: "Credit Risk",
    accent: "0.68 0.2 30",
    icon: <Gauge className="size-5" />,
    blurb: "Internal ratings and call-report health — feeds the early-warning model.",
    tables: [
      {
        name: "member_credit_ratings",
        grain: "rating history",
        desc: "Internal rating history with next-review cadence.",
        pk: "rating_id",
        fks: ["member_id → members", "rating_model_id → ops_model_inventory"],
      },
      {
        name: "call_reports_quarterly",
        grain: "member × quarter",
        desc: "FFIEC call-report metrics; some planted deterioration.",
        pk: "report_id",
        fks: ["member_id → members"],
      },
    ],
  },
  {
    id: "mortgage",
    name: "Mortgage & MPF",
    accent: "0.7 0.16 300",
    icon: <Home className="size-5" />,
    blurb: "Origination activity and the acquired-member-asset loan book.",
    tables: [
      {
        name: "mortgage_originations",
        grain: "member × month",
        desc: "Monthly originations with secondary-market outlet.",
        pk: "origination_id",
        fks: ["member_id → members"],
      },
      {
        name: "mpf_loans",
        grain: "1 row / loan",
        desc: "MPF / acquired-member-asset loan book held by the Bank.",
        pk: "loan_id",
        fks: ["member_id → members"],
      },
      {
        name: "mpf_servicing_monthly",
        grain: "loan × month",
        desc: "Monthly servicing / delinquency by loan and vintage.",
        pk: "servicing_id",
        fks: ["loan_id → mpf_loans"],
      },
    ],
  },
  {
    id: "treasury",
    name: "Investments & Funding",
    accent: "0.62 0.16 275",
    icon: <TrendingUp className="size-5" />,
    blurb: "The investment portfolio, funding curve, and bank-level position.",
    tables: [
      {
        name: "investment_holdings",
        grain: "1 row / holding",
        desc: "Agency MBS positions with unrealized gain/loss.",
        pk: "holding_id",
      },
      {
        name: "prepayment_speeds",
        grain: "portfolio × month",
        desc: "Actual vs forecast prepayment speeds (CPR).",
        pk: "prepay_id",
      },
      {
        name: "co_issuances",
        grain: "1 row / issuance",
        desc: "Consolidated obligation issuances with spread to Treasuries.",
        pk: "issuance_id",
      },
      {
        name: "market_rates_daily",
        grain: "1 row / day",
        desc: "Daily SOFR and Treasury curve points.",
        pk: "business_date",
      },
      {
        name: "bank_position_daily",
        grain: "1 row / day",
        desc: "Bank-level balance-sheet snapshot; mission-asset ratio.",
        pk: "business_date",
      },
    ],
  },
  {
    id: "planning",
    name: "Financial Planning",
    accent: "0.7 0.12 195",
    icon: <PiggyBank className="size-5" />,
    blurb: "Actuals vs plan across financials, spend, and capital.",
    tables: [
      {
        name: "financials_actual_vs_forecast",
        grain: "line × quarter",
        desc: "Actual vs forecast financial line items by quarter.",
        pk: "fin_id",
      },
      {
        name: "vendor_spend",
        grain: "category × month",
        desc: "Vendor / contractual services spend vs plan (YTD).",
        pk: "spend_id",
      },
      {
        name: "capital_plan",
        grain: "1 row / quarter",
        desc: "Retained earnings vs target and activity-based stock.",
        pk: "quarter_end_date",
      },
    ],
  },
  {
    id: "mission",
    name: "Affordable Housing & Mission",
    accent: "0.75 0.15 155",
    icon: <HeartHandshake className="size-5" />,
    blurb: "AHP pipeline, set-aside, community investment, and the pledge.",
    tables: [
      {
        name: "ahp_applications",
        grain: "1 row / application",
        desc: "AHP applications through the funding pipeline.",
        pk: "application_id",
      },
      {
        name: "homeownership_setaside",
        grain: "1 row / allocation",
        desc: "Down-payment assistance allocations by member.",
        pk: "allocation_id",
        fks: ["member_id → members"],
      },
      {
        name: "cip_cica_activity",
        grain: "1 row / activity",
        desc: "Community Investment / Cash Advance activity.",
        pk: "activity_id",
      },
      {
        name: "mission_units",
        grain: "tier × rural flag",
        desc: "Housing units supported by income tier (FHFA format).",
        pk: "mission_unit_id",
      },
      {
        name: "pledge_activity",
        grain: "program × state × month",
        desc: "Progress toward the $200M affordability pledge.",
        pk: "pledge_id",
      },
    ],
  },
  {
    id: "engagement",
    name: "Member Engagement",
    accent: "0.8 0.16 85",
    icon: <MousePointerClick className="size-5" />,
    blurb: "How members use the eAdvantage portal — and where they go quiet.",
    tables: [
      {
        name: "eadvantage_activity",
        grain: "1 row / session",
        desc: "Portal session activity; spot login-but-no-transact members.",
        pk: "session_id",
        fks: ["member_id → members"],
      },
    ],
  },
  {
    id: "governance",
    name: "Governance & Operations",
    accent: "0.68 0.19 300",
    icon: <ShieldCheck className="size-5" />,
    blurb: "The exam-ready backbone: sources, lineage, quality, access, and cost.",
    tables: [
      {
        name: "ops_source_systems",
        grain: "1 row / system",
        desc: "Source-system inventory feeding the data estate.",
        pk: "source_system_id",
      },
      {
        name: "ops_data_quality_exceptions",
        grain: "1 row / exception",
        desc: "DQ exceptions on regulatory reports, traced to source.",
        pk: "exception_id",
        fks: ["source_system_id → ops_source_systems"],
      },
      {
        name: "ops_column_lineage",
        grain: "1 row / edge",
        desc: "Column-level lineage for the credit-rating field.",
        pk: "lineage_id",
        fks: ["source_system_id → ops_source_systems"],
      },
      {
        name: "ops_bi_refresh",
        grain: "dashboard × day",
        desc: "Qlik / Power BI refresh log with SLA status.",
        pk: "refresh_id",
      },
      {
        name: "ops_metric_reconciliation",
        grain: "1 row / metric",
        desc: "Same metric across BI tools vs authoritative Lakehouse.",
        pk: "reconciliation_id",
      },
      {
        name: "ops_access_events",
        grain: "1 row / event",
        desc: "Access log for nonpublic member financial data.",
        pk: "event_id",
        fks: ["member_id → members"],
      },
      {
        name: "ops_model_inventory",
        grain: "1 row / model",
        desc: "Model inventory with validation dates (FHFA MRM).",
        pk: "model_id",
      },
      {
        name: "ops_examiner_requests",
        grain: "1 row / request",
        desc: "Examiner data-request log with turnaround by type.",
        pk: "request_id",
      },
      {
        name: "ops_pipeline_cost",
        grain: "pipeline × month",
        desc: "Monthly pipeline run cost; dual-run legacy + Fabric.",
        pk: "cost_id",
      },
      {
        name: "ops_gl_reconciliation",
        grain: "1 row / recon",
        desc: "eAdvantage feeds reconciled against the general ledger.",
        pk: "recon_id",
      },
      {
        name: "ops_ai_content_sources",
        grain: "1 row / source",
        desc: "Content-source registry for the AHP virtual assistant.",
        pk: "source_id",
      },
    ],
  },
];

const TABLE_COUNT = DOMAINS.reduce((n, d) => n + d.tables.length, 0);

function TableRow({ t }: { t: Table }) {
  return (
    <li className="rounded-xl border border-border/50 bg-background/40 p-3">
      <div className="flex items-center justify-between gap-2">
        <code className="text-[12.5px] font-semibold text-foreground">{t.name}</code>
        <span className="shrink-0 rounded-full border border-border/60 bg-background/60 px-2 py-0.5 text-[10px] text-muted-foreground">
          {t.grain}
        </span>
      </div>
      <p className="mt-1 text-[11.5px] leading-snug text-muted-foreground">{t.desc}</p>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="persona-bg-soft persona-text inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium">
          <KeyRound className="size-2.5" /> {t.pk}
        </span>
        {t.fks?.map((fk) => (
          <span
            key={fk}
            className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-background/60 px-1.5 py-0.5 text-[10px] text-muted-foreground"
          >
            <Link2 className="size-2.5" /> {fk}
          </span>
        ))}
      </div>
    </li>
  );
}

function DomainCard({ d, index }: { d: Domain; index: number }) {
  return (
    <div
      className="animate-fade-up glass-persona flex flex-col gap-3 rounded-2xl p-4"
      style={{
        ["--persona" as string]: `oklch(${d.accent})`,
        animationDelay: `${120 + index * 70}ms`,
      }}
    >
      <div className="flex items-center gap-3">
        <div className="persona-bg-soft persona-text grid size-11 shrink-0 place-items-center rounded-xl">
          {d.icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold">{d.name}</div>
            <span className="persona-text text-[11px] font-semibold">
              {d.tables.length} {d.tables.length === 1 ? "table" : "tables"}
            </span>
          </div>
          <div className="text-[11px] leading-snug text-muted-foreground">{d.blurb}</div>
        </div>
      </div>
      <ul className="space-y-2">
        {d.tables.map((t) => (
          <TableRow key={t.name} t={t} />
        ))}
      </ul>
    </div>
  );
}

function DataModelView() {
  return (
    <div
      className="mx-auto max-w-6xl space-y-4"
      style={{ ["--persona" as string]: `oklch(${BLUE})` }}
    >
      {/* Intro */}
      <div className="animate-fade-up text-center">
        <div className="persona-text mb-1 flex items-center justify-center gap-1.5 text-xs font-semibold uppercase tracking-widest">
          <Database className="size-3.5" /> One governed catalog
        </div>
        <h2 className="gradient-text text-2xl font-semibold tracking-tight">
          The FHLB data model, by domain
        </h2>
        <p className="mx-auto mt-1 max-w-2xl text-sm text-muted-foreground">
          Every cockpit reads from <code className="text-foreground/90">fhlb.des_moines</code> —
          one Unity Catalog schema. The <code className="text-foreground/90">members</code> table
          is the spine; each domain joins back on <code className="text-foreground/90">member_id</code>.
        </p>
      </div>

      {/* Stat strip */}
      <div
        className="animate-fade-up glass mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-x-6 gap-y-2 rounded-2xl px-4 py-3 text-center"
        style={{ animationDelay: "60ms" }}
      >
        <Stat icon={<Database className="size-4" />} value={`${TABLE_COUNT}`} label="tables" />
        <Stat icon={<Layers className="size-4" />} value={`${DOMAINS.length}`} label="domains" />
        <Stat icon={<KeyRound className="size-4" />} value="fhlb.des_moines" label="Unity Catalog schema" />
        <Stat icon={<ShieldCheck className="size-4" />} value="Governed" label="lineage + access controls" />
      </div>

      {/* Domain grid */}
      <div className="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
        {DOMAINS.map((d, i) => (
          <DomainCard key={d.id} d={d} index={i} />
        ))}
      </div>
    </div>
  );
}

function Stat({ icon, value, label }: { icon: ReactNode; value: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="persona-text">{icon}</span>
      <div className="text-left leading-tight">
        <div className="text-sm font-semibold text-foreground">{value}</div>
        <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}
