"""
Create five persona Genie Spaces over fhlb.des_moines using the Databricks CLI
(`databricks genie create-space`). Each space gets its tables, an instructions
block (vocabulary + join guidance), and sample questions taken from the demo doc
and rewritten to the actual column names.

Run:
  uv run python data_generation/create_genie_spaces.py
"""
import json
import os
import subprocess
import tempfile
import uuid

PROFILE = "fevm-serverless-stable-blj52t"
WAREHOUSE_ID = "688f49c732cf9083"
DBX = "/opt/homebrew/bin/databricks"
CAT = "fhlb.des_moines"


def hid() -> str:
    return uuid.uuid4().hex


def T(*names):
    return [{"identifier": f"{CAT}.{n}"} for n in sorted(names)]


def questions(*qs):
    return [{"id": hid(), "question": [q]} for q in qs]


def instr(text: str):
    return {"text_instructions": [{"id": hid(), "content": [text]}]}


SPACES = [
    {
        "title": "FHLB Des Moines - Credit & Collateral (CRO)",
        "description": "Synthetic member credit, collateral, and evidence-velocity analytics keyed to AB 2024-03. Fictional demo data.",
        "tables": T("members", "member_credit_ratings", "call_reports_quarterly", "pledged_collateral",
                    "collateral_reviews", "advance_daily_balances", "letters_of_credit", "mpf_loans",
                    "mpf_servicing_monthly", "ops_model_inventory"),
        "instructions": (
            "You are a credit-risk analytics assistant for the FHLB Des Moines Chief Risk Officer. All data is synthetic.\n"
            "Vocabulary: 'advances' are secured loans to members; 'overcollateralization (OC) cushion' or 'unused capacity' "
            "= pledged_collateral.lendable_value_usd minus a member's advances outstanding; 'AB 2024-03 cadence' means a "
            "credit rating is overdue when member_credit_ratings.next_review_due < current_date; 'High Level Concern' is "
            "mpf_servicing_monthly.high_level_concern_flag.\n"
            "Joins: all member tables join on member_id to members. For current advances, take the latest business_date in "
            "advance_daily_balances and SUM(outstanding_par_usd) by member_id. For current ratings, take the row per "
            "member with MAX(as_of_date) in member_credit_ratings. call_reports_quarterly is one row per member per "
            "quarter_end_date; compute quarter-over-quarter deterioration by comparing consecutive quarters. "
            "mpf_servicing_monthly joins mpf_loans on loan_id and members on member_id (the PFI).\n"
            "Concentration = top borrowers' SUM(outstanding_par_usd) as a share of the total. Insurance exposure filters "
            "members.member_type = 'Insurance Company'. Rank 'sharpest deterioration' using uninsured_deposit_ratio_pct, "
            "brokered_deposit_growth_pct, and unrealized_securities_loss_usd. Models past due: "
            "ops_model_inventory.validation_due_date < current_date."
        ),
        "questions": questions(
            "Which members' credit ratings are past the AB 2024-03 refresh cadence, ranked by advances outstanding?",
            "Which members showed the sharpest quarter-over-quarter deterioration in uninsured deposit ratio, brokered deposit growth, or unrealized securities losses?",
            "Which borrowers' overcollateralization cushions are thinnest, measured as lendable collateral minus advances outstanding?",
            "What is our concentration exposure: the top ten borrowers as a share of total advances?",
            "What are the delinquency and High Level Concern trends on MPF loans by PFI and vintage year?",
            "Which credit and collateral models are past due for validation?",
            "Which borrowing members also show Federal Reserve facility usage signals in their call report data?",
            "Which pledged collateral types had the highest exception rates in the most recent collateral reviews?",
        ),
    },
    {
        "title": "FHLB Des Moines - Finance & Treasury (CFO)",
        "description": "Synthetic forecasting, spread, dividend, and expense analytics. Fictional demo data.",
        "tables": T("bank_position_daily", "market_rates_daily", "advance_pricing_daily", "co_issuances",
                    "advance_daily_balances", "advance_forecast_quarterly", "financials_actual_vs_forecast",
                    "vendor_spend", "capital_plan", "investment_holdings", "prepayment_speeds", "members"),
        "instructions": (
            "You are a treasury and financial-planning assistant for the FHLB Des Moines CFO. All data is synthetic.\n"
            "Vocabulary: 'CO' = consolidated obligations; 'core mission asset ratio' = "
            "(bank_position_daily.total_advances_usd + total_ama_usd) / consolidated_obligations_usd; 'net interest spread' "
            "is a line_item in financials_actual_vs_forecast (stored in percent, not dollars); SOFR and Treasury yields are "
            "in market_rates_daily; advance vs member-alternative pricing by maturity is advance_pricing_daily "
            "(advance_rate_pct vs brokered_deposit_rate_pct by tenor_months).\n"
            "Joins: advance_daily_balances joins members on member_id; segment = members.member_type. For 'as of this "
            "morning' use the latest business_date. Compare advance balances to advance_forecast_quarterly by member_segment "
            "and quarter_end_date. Forecast variance uses financials_actual_vs_forecast (actual_value, forecast_value, "
            "variance_value) by quarter_end_date and line_item. Unrealized gain/loss is investment_holdings "
            "unrealized_gain_loss_usd by vintage_year and duration_bucket. Prepayment actual vs forecast is "
            "prepayment_speeds actual_cpr_pct vs forecast_cpr_pct by portfolio."
        ),
        "questions": questions(
            "What are total advance balances as of the latest business date by member segment, and how do they compare to the quarterly forecast?",
            "Which members drove the largest advance balance movements over the last week?",
            "How do this week's consolidated obligation issuance spreads to Treasuries compare to the trailing 90 days?",
            "What are actual prepayment speeds versus the forecast assumptions by portfolio?",
            "What is the unrealized gain or loss on the agency MBS portfolio by vintage year and duration bucket?",
            "What was our net income forecast variance for each of the last four quarters, and which line items drove the misses?",
            "Where is contractual services and professional fees spend running against plan year to date, and which vendor categories are growing fastest?",
            "What is retained earnings adequacy against the capital plan target by quarter?",
        ),
    },
    {
        "title": "FHLB Des Moines - Member & Products (CBO)",
        "description": "Synthetic member growth, retention, and product-uptake analytics across the district. Fictional demo data.",
        "tables": T("members", "eligible_nonmembers", "advance_daily_balances", "pledged_collateral",
                    "letters_of_credit", "mortgage_originations", "mpf_loans", "eadvantage_activity"),
        "instructions": (
            "You are a member-growth analytics assistant for the FHLB Des Moines Chief Business Officer. All data is synthetic.\n"
            "Vocabulary: 'unused borrowing capacity' = pledged_collateral.lendable_value_usd minus advances outstanding; "
            "'MPF leakage' = members in mortgage_originations with sold_to <> 'MPF' (they route to Fannie/Freddie/Ginnie "
            "instead); 'churn signal' = members whose activity is declining across advances, letters_of_credit, and MPF; "
            "'eAdvantage lurkers' = members with recent logins but no transaction in 90 days.\n"
            "Joins: everything joins members on member_id. Advance utilization = SUM(outstanding_par_usd) at latest "
            "business_date grouped by members.member_type and members.charter_state. mortgage_originations has monthly "
            "loan_count, origination_volume_usd, and sold_to; MPF delivery volume trends filter sold_to = 'MPF'. "
            "eadvantage_activity has action_type ('Login','View','Transaction') and transacted_flag; a lurker has logins "
            "but MAX(session_date where transacted_flag) older than 90 days. eligible_nonmembers.similarity_score (0-100) "
            "ranks prospects that look like the best members."
        ),
        "questions": questions(
            "What is advance utilization by member type and state at the latest date?",
            "Which members have the largest unused borrowing capacity based on pledged collateral versus advances outstanding?",
            "Which members are originating mortgages but not delivering into the MPF Program, and what outlet are they using instead?",
            "Which Participating Financial Institutions increased or decreased MPF delivery volume the most this year?",
            "Which members show declining activity across advances, letters of credit, and MPF together?",
            "What does letter of credit usage look like by purpose, and which member segments are underpenetrated?",
            "Which members logged into eAdvantage recently but have not transacted in 90 days?",
            "Which eligible nonmembers look most like our best-performing members, ranked by similarity score?",
        ),
    },
    {
        "title": "FHLB Des Moines - Mission & AHP (Community Investment)",
        "description": "Synthetic community investment and mission analytics: the $200M pledge, AHP pipeline, and FHFA mission reporting. Fictional demo data.",
        "tables": T("ahp_applications", "homeownership_setaside", "cip_cica_activity", "mission_units",
                    "pledge_activity", "mpf_loans", "members"),
        "instructions": (
            "You are a community-investment analytics assistant for FHLB Des Moines. All data is synthetic.\n"
            "Vocabulary: the '$200M pledge' progress is in pledge_activity (committed_usd, disbursed_usd) by program, state, "
            "and activity_month; 'subsidy per unit' is ahp_applications.subsidy_per_unit_usd (lower is more efficient); "
            "'need for subsidy' is ahp_applications.need_for_subsidy_ratio for rentals where a value below 1 suggests "
            "overfunding; 'high-need geography' is ahp_applications.tclp_high_need_flag (Targeted Community Lending Plan); "
            "'set-aside' programs are in homeownership_setaside (allocated_usd, used_usd, expiration_date); income tiers in "
            "mission_units are 'Very Low Income' and 'Low or Moderate Income' with a rural_flag; FHFA housing goals on AMA "
            "purchases use mpf_loans.low_income_flag and low_income_area_flag.\n"
            "Joins: ahp_applications, homeownership_setaside, cip_cica_activity join members on member_id. The AHP pipeline "
            "funnel uses ahp_applications.status (Received, Scored, Awarded, Disbursed, At Risk of Close, De-obligated). "
            "Units per subsidy dollar = units_total / subsidy_requested_usd."
        ),
        "questions": questions(
            "What is year-to-date progress against the $200 million housing affordability pledge, broken out by program and by state?",
            "What is the AHP pipeline by status: applications received, scored, awarded, and disbursed, with the subsidy-per-unit distribution?",
            "Which competitive AHP applications deliver the most units per subsidy dollar in high-need geographies?",
            "For rental project awards, which applications show a genuine need for subsidy and which look overfunded?",
            "What is uptake on the homeownership set-aside programs by member, and which members have unused allocations expiring?",
            "What is Community Investment Program and CICA volume year to date, split between housing and economic development?",
            "How many units have we supported this year by income tier, very low income versus low or moderate income, and what share are rural?",
            "How are we tracking against FHFA housing goals on our MPF purchases, specifically the low-income and low-income-area shares?",
        ),
    },
    {
        "title": "FHLB Des Moines - Data Governance & Operations (CIO)",
        "description": "Synthetic operational, governance, and exam-evidence analytics across the data estate. Fictional demo data.",
        "tables": T("ops_data_quality_exceptions", "ops_source_systems", "ops_column_lineage", "ops_bi_refresh",
                    "ops_metric_reconciliation", "ops_access_events", "ops_model_inventory", "ops_examiner_requests",
                    "ops_pipeline_cost", "ops_gl_reconciliation", "ops_ai_content_sources"),
        "instructions": (
            "You are a data-governance and operations assistant for the FHLB Des Moines Chief Information and Operations "
            "Officer. All data is synthetic.\n"
            "Vocabulary: the estate includes 16 legacy SQL Server instances plus a Microsoft Fabric build "
            "(ops_source_systems); a 'dual run' pipeline has ops_pipeline_cost.is_dual_run_flag = true and appears on both "
            "platforms; an 'SLA miss' is ops_bi_refresh.sla_met_flag = false; a 'metric mismatch' is "
            "ops_metric_reconciliation.mismatch_flag = true (compare qlik_value and powerbi_value to authoritative_value); "
            "'out of policy access' is ops_access_events.in_policy_flag = false on data_classification = "
            "'Nonpublic Member Financial'; a model is overdue when ops_model_inventory.validation_due_date < current_date; "
            "'evidence velocity' is ops_examiner_requests.turnaround_days compared across exam_cycle.\n"
            "Joins: ops_data_quality_exceptions and ops_column_lineage join ops_source_systems on source_system_id. Open "
            "exceptions this quarter filter status = 'Open'. Lineage for the member credit rating field filters "
            "ops_column_lineage.field_name = 'member_credit_rating' ordered by layer. Dual-run cost sums monthly_cost_usd "
            "across both platforms for is_dual_run_flag pipelines. The Affordable Housing Virtual Assistant governance is in "
            "ops_ai_content_sources (content_source, approver, governed_flag)."
        ),
        "questions": questions(
            "Which reports due to the FHFA this quarter have open data quality exceptions, and which SQL Server instances do those exceptions trace back to?",
            "Show the full lineage for the member credit rating field, from source ingestion to the reported value.",
            "Which Qlik and Power BI dashboards missed their refresh SLA in the last 30 days, and which extract jobs caused the misses?",
            "Where are Qlik and Power BI showing different values for the same metric, and which source table is authoritative?",
            "Who accessed nonpublic member financial data in the last 90 days, and were any of those accesses outside role-based policy?",
            "Which production models touch member data, and when was each last validated?",
            "What is our average turnaround time on examiner data requests this exam cycle versus last, by request type?",
            "Which pipelines run in parallel on both SQL Server and Microsoft Fabric, and what is the monthly cost of the dual run?",
            "What data feeds eAdvantage member-facing screens, and when was each feed last reconciled against the general ledger?",
            "What content sources does the Affordable Housing Virtual Assistant draw on, and who approved each one?",
        ),
    },
]


def build_serialized(space) -> str:
    return json.dumps({
        "version": 2,
        "config": {"sample_questions": space["questions"]},
        "data_sources": {"tables": space["tables"]},
        "instructions": space["instructions_block"],
    })


def create_space(space) -> dict:
    space["instructions_block"] = instr(space["instructions"])
    serialized = build_serialized(space)
    body = {
        "warehouse_id": WAREHOUSE_ID,
        "serialized_space": serialized,
        "title": space["title"],
        "description": space["description"],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        path = f.name
    out = subprocess.run(
        [DBX, "genie", "create-space", "--json", f"@{path}", "--profile", PROFILE, "-o", "json"],
        capture_output=True, text=True,
        env={**os.environ, "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
             "DATABRICKS_CLI_DO_NOT_EXECUTE_NEWER_VERSION": "1"},
    )
    if out.returncode != 0:
        return {"error": (out.stderr or out.stdout)[:500], "title": space["title"]}
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"raw": out.stdout[:500], "title": space["title"]}


if __name__ == "__main__":
    results = []
    for sp in SPACES:
        print(f"Creating: {sp['title']} ({len(sp['tables'])} tables, {len(sp['questions'])} questions)...")
        r = create_space(sp)
        sid = r.get("space_id")
        if sid:
            host = "https://fevm-serverless-stable-blj52t.cloud.databricks.com"
            print(f"  space_id={sid}")
            print(f"  URL: {host}/genie/rooms/{sid}")
        else:
            print(f"  FAILED: {r.get('error') or r.get('raw')}")
        results.append((sp["title"], sid, r))
    print("\n=== SUMMARY ===")
    for title, sid, r in results:
        print(f"{'OK ' if sid else 'ERR'} {title}: {sid or r.get('error')}")
