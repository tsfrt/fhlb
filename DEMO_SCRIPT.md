# FHLB Des Moines — Executive Command Center
## Live Demo Script (Business Impact Walkthrough)

**Audience:** FHLB Des Moines leadership (CEO/Board, CFO, CRO, CBO, CIO, Community Investment)
**Duration:** ~18–22 minutes
**Environment:** https://fhlb-command-center-7474656503943141.aws.databricksapps.com
**Platform story:** One governed app over the Databricks platform — **Lakehouse** (live data), **Lakeflow Declarative Pipelines** (the data model, built as a visual dependency graph of materialized views), **Genie** (natural-language + deep-research agent), **AI Gateway** (governed LLM), **Model Serving** (classical ML credit-risk model), **Lakebase** (Postgres app state), **Databricks Apps** (React + FastAPI).

> **One-sentence pitch:** *"Every seat on your leadership team gets a live, governed cockpit over the same warehouse of record — with an AI research agent that finds the problems before the examiner or the market does."*

---

## 0. Setup & framing (1 min)

**Say:**
> "What you're about to see is a single application that sits directly on your lakehouse. There are no extracts, no overnight batch, no spreadsheets emailed around. Each executive sees their own cockpit, but every number traces to the same governed source of truth. And the AI you'll see is governed — it can only touch approved, permissioned data, and every call is audited."

**Do:** Land on the **Executive Overview**. Point out the left rail: one cockpit per leader, plus an **Architecture** tab.

**Business impact to plant early:** *Decision latency drops from days to seconds; governance and AI are built-in, not bolted on.*

---

## 1. Executive Overview — "The whole Bank, as of this morning" (3 min)
*Audience: Board & CEO*

**Screen:** KPI band, District map, AI briefing, AI Anomaly Radar, live alert feed.

**Do & Say:**
1. **KPI band** — "Five numbers that define the Bank this morning: **Total Advances**, **Core Mission Asset Ratio**, **$200M Affordable Housing Pledge YTD**, **Open FHFA Exam Exceptions**, and **At-Risk Members**. These are live off the warehouse — refresh and they move."
2. **This morning's briefing** — "This is written by a governed LLM through the **AI Gateway**, grounded on the live numbers — not a canned paragraph. Notice it cites concrete figures and flags the single most important change." (Toggle engine to **Genie deep research** if you want to show it investigating the data itself, with citations.)
3. **AI Anomaly Radar** — expand it. "This is a Genie **research agent** that scanned the Bank overnight and surfaced the anomalies worth investigating — ranked High/Medium/Low. It cached the result so it runs once a day, not on every click." Click **Investigate** on a finding → the side panel opens and the agent digs into that specific issue with the exact query that surfaced it.
4. **District map + alert feed** — "13 states plus the Pacific territories, advances by charter state. Alerts are acknowledged right here and the acknowledgement **persists to Lakebase** — this is a system of engagement, not just a dashboard."

**Business impact:**
- **Board-ready situational awareness in one screen** — no pre-meeting deck assembly.
- **Proactive risk surfacing** — the AI finds the issue before it becomes a headline or an exam finding.
- **Accountability** — acknowledgements and AI calls are logged.

---

## 2. CFO — Finance & Treasury: "Balance sheet & mission on one screen" (3 min)
*Audience: James Livingston, CFO*

**Screen:** Advances vs Forecast, Core Mission Asset Ratio, interactive SOFR sensitivity, CO spreads, unrealized MBS G/L.

**Do & Say:**
1. **Advances vs Forecast** — "Actuals against the treasury plan, by quarter. Variance is visible immediately."
2. **± SOFR Rate Sensitivity** — drag the slider. "This is a live **what-if**: shift SOFR ±100 bps and watch the estimated annual NII impact on the floating book recompute against real balances. Your ALCO conversation, interactive."
3. **Core Mission Asset Ratio & CO spreads** — "Mission compliance and funding cost trends side by side."
4. **Unrealized MBS G/L by vintage** — "Mark-to-market exposure by vintage, at a glance."

**Business impact:**
- **Faster, defensible ALCO/treasury decisions** — rate scenarios in seconds, not a modeling cycle.
- **Mission + margin in one view** — balance the regulatory mandate against profitability without switching tools.

---

## 3. CRO — Credit & Collateral: "Where credit risk is concentrating" (3 min)
*Audience: Joelyn Jensen-Marren, CRO*

**Screen:** Member Early-Warning (ML), Ratings past cadence, Member Watchlist (Lakebase), thinning OC cushion, advance concentration, MPF delinquency trend.

**Do & Say:**
1. **Member Early-Warning (ML)** — "This is a credit-risk model — XGBoost, registered in **Unity Catalog** and served on **Databricks Model Serving** — scoring every member's probability of 12-month deterioration. It ranks the book by risk *before* the internal rating moves. Notice the **RATING GAP** flags: members still rated Strong or Satisfactory that the model already puts in the High band. Expand one and it shows the **top drivers** — rising uninsured deposits, thinning OC cushion — straight from the model's SHAP contributions. One click adds them to the watchlist. And it's a real API: hit **Rescore** and it scores live against the endpoint."
2. **Ratings past AB 2024-03 cadence** — "Members overdue for a credit review, ranked by advances outstanding — so you triage by exposure, not alphabetically. Add one to the **watchlist** with a click."
3. **Member Watchlist** — "That watchlist is **persisted in Lakebase** — it's shared team state, survives refreshes, and is auditable."
4. **Thinning OC cushion & concentration** — "Where collateral coverage is thinning, and how concentrated the book is in the top 10 members — your two biggest tail risks on one screen."
5. **MPF delinquency trend** — stacked by bucket over 12 months.
6. **Anomaly Radar → Investigate** — "Let the research agent confirm whether a concentration spike is a real risk or a data artifact, and tell you which members are driving it."

**Platform story to plant:** *Genie investigates the book conversationally; this is the production risk engine — a versioned model in Unity Catalog, served as an API, exactly the pattern model risk management (FHFA AB 2013-07) expects.*

**Business impact:**
- **Predictive, not just descriptive** — the model surfaces deterioration before the rating cadence catches it.
- **Exposure-weighted risk triage** — attention goes where the dollars are.
- **Shared, persistent risk workflow** — watchlist as a living record, not a personal spreadsheet.
- **Earlier intervention** on deteriorating collateral and concentration.

---

## 4. CBO — Member & Products: "Grow the wallet with every member" (2.5 min)
*Audience: Wil Osborn, CBO*

**Screen:** Advance utilization by product, unused borrowing capacity (whitespace), MPF leakage, eAdvantage lurkers, prospect lookalikes.

**Do & Say:**
1. **Unused Borrowing Capacity** — "This is pure **whitespace**: lendable collateral minus current advances, by member. This is your call list for Monday."
2. **MPF Leakage** — "Members originating mortgages but selling them somewhere other than MPF — quantified revenue we're leaving on the table."
3. **eAdvantage Lurkers** — "Active on the portal but not transacting — warm engagement, no conversion."
4. **Prospect Lookalikes** — "Eligible non-members ranked by similarity to your best borrowers — a data-driven prospect list."

**Business impact:**
- **Concrete revenue expansion targets** — whitespace, leakage, and lookalikes turn analytics into a sales motion.
- **Retention signal** — engaged-but-idle members flagged before they churn.

---

## 5. CIO — Data Governance & Operations: "Governed data, ready for the examiner" (3 min)
*Audience: Kevin Larkin, CIO*

**Screen:** Open FHFA DQ exceptions, dual-run platform cost, BI refresh SLA, model validation backlog, out-of-policy access, lineage viewer, examiner evidence pack.

**Do & Say:**
1. **Open FHFA Data Quality Exceptions** — "Traced back to the source SQL Server instance. When the examiner asks 'why is this number wrong,' you have the answer, not a research project."
2. **Lineage Viewer** — "End-to-end lineage for a regulated field — Unity Catalog governance made visible."
3. **Dual-Run Platform Cost** — "The monthly cost of running the legacy stack alongside the migration — the business case for consolidation, quantified."
4. **Examiner Evidence Pack** — "Assemble artifacts for an FHFA request and **persist them in Lakebase**. The exam prep that used to take a week is a running, shareable pack."
5. **Model backlog & out-of-policy access** — "Validation debt and access-policy breaches, surfaced continuously."

**Business impact:**
- **Exam readiness on demand** — lineage + evidence packs collapse audit prep time and risk.
- **Migration ROI, quantified** — dual-run cost makes the consolidation decision objective.
- **Continuous control monitoring** — governance is observed, not assumed.

---

## 6. Mission & Affordable Housing: "The $200M pledge, in motion" (2.5 min)
*Audience: Community Investment*

**Screen:** $200M pledge gauge, Governed Affordable Housing Assistant, AHP funnel, subsidy efficiency, units by income tier.

**Do & Say:**
1. **$200M Pledge gauge** — "Live progress against the public commitment, by program. This is the number you report to the community and the regulator."
2. **Governed Affordable Housing Assistant** — ask it a question. "This assistant answers **only from approved, governed content sources** through the AI Gateway. Ask it something off-topic and it declines — that's the guardrail. No hallucinated policy."
3. **Subsidy efficiency & units by income tier** — "Dollars per unit by project type, and affordable units delivered rural vs non-rural by income tier — mission impact you can defend."

**Business impact:**
- **Transparent mission accountability** — pledge progress and impact are always current.
- **Safe public-facing AI** — governed answers protect the brand and the mandate.

---

## 7. Architecture tab — "How it all fits" (1.5 min)
*Audience: technical stakeholders / CIO*

**Do & Say:** Open **Architecture**. "One app, the whole platform: **Lakehouse** is the source of truth; **Genie** powers natural-language and the deep-research agent; the **AI Gateway** governs every LLM call with PII controls, rate limits, and inference logging; **Model Serving** hosts the classical ML credit-risk model registered in Unity Catalog; **Lakebase** (Postgres) holds app state like the watchlist and exam packs; and it's all delivered as a **Databricks App** — React + FastAPI — running next to the data."

**Do & Say (Data Model tab):** Open **Data Model**. "Every table you've seen lives in one governed Unity Catalog schema, `fhlb.des_moines`, grouped by domain with `members` as the spine. And it isn't hand-loaded — it's populated by a **Lakeflow Spark Declarative Pipeline**: 38 materialized views wired into a dependency graph (members → advances → collateral, mortgage → MPF → servicing, source systems → data-quality lineage). Open the pipeline in Lakeflow and you can watch the whole model rebuild as a visual DAG — that's the data-engineering backbone under the cockpits."

**Business impact:** *No new data silo, no ungoverned AI, no extra vendor — it runs where your data and your controls already live.*

---

## 8. Close (1 min)

**Say:**
> "Everything you saw is one governed application on your lakehouse. The same numbers, for every leader, in real time — with an AI research agent that hunts for the problems, an assistant that's safe to put in front of the public, and a full audit trail behind every AI call. This is what it looks like to run the Bank on a governed, AI-native data platform."

**Leave-behind talking points:**
- **Real-time, single source of truth** — decisions in seconds, no reconciliation.
- **Governed AI** — grounded, permissioned, audited; Genie deep-research finds risk proactively.
- **System of engagement** — watchlists, acknowledgements, and exam packs persist in Lakebase.
- **Exam-ready** — lineage and evidence packs collapse audit prep.
- **Growth + mission + risk** — one platform serves all three mandates.

---

## Appendix — Feature "wow" moments to hit
| Moment | Where | Why it lands |
|---|---|---|
| Interactive SOFR NII what-if | CFO | Live modeling on real balances |
| Member Early-Warning + **rating gap** | CRO | Governed ML on Model Serving, ahead of the rating |
| AI Anomaly Radar + **Investigate** | Every cockpit | Agentic AI that finds and root-causes issues |
| Genie deep-research (Agent mode) | Side panel | Multi-step SQL research with cited report |
| Governed assistant declines off-topic | Mission | Proves the guardrail is real |
| Watchlist / Exam pack persistence | CRO / CIO | Lakebase = system of engagement |
| Lineage + DQ exception → source | CIO | Instant exam answers |
| Whitespace / MPF leakage | CBO | Analytics → revenue action |

## Appendix — Demo hygiene
- **Pre-warm the Anomaly Radar** for the cockpits you'll show (open each once so the daily scan is cached and appears instantly).
- Have one **Investigate** click ready per persona to show the agent live.
- If Agent mode is slow on the day, lead with the cached radar summary and the standard Genie chat.
- Keep the **Architecture** tab for the technical audience; skip for a pure business room if time is tight.
