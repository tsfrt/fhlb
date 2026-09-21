"""SQL query catalog for fhlb.des_moines. All KPIs and charts are real queries
executed via the Statement Execution API. Each function returns a SQL string;
the router runs it and returns rows to the frontend.
"""
from __future__ import annotations

from ..core._config import AppConfig


def _s(cfg: AppConfig) -> str:
    return f"{cfg.catalog}.{cfg.schema_name}"


# --------------------------------------------------------------------------- #
# Shared / Overview                                                            #
# --------------------------------------------------------------------------- #

def freshness(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"SELECT MAX(business_date) AS as_of FROM {s}.advance_daily_balances"


def overview_kpis(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH latest AS (SELECT MAX(business_date) d FROM {s}.bank_position_daily),
pos AS (
  SELECT total_advances_usd, total_ama_usd, consolidated_obligations_usd, net_income_mtd_usd
  FROM {s}.bank_position_daily WHERE business_date=(SELECT d FROM latest)
),
pledge AS (
  SELECT SUM(disbursed_usd) ytd_disbursed
  FROM {s}.pledge_activity WHERE YEAR(activity_month)=YEAR(CURRENT_DATE)
),
dq AS (SELECT COUNT(*) open_exceptions FROM {s}.ops_data_quality_exceptions WHERE status='Open'),
atrisk AS (
  SELECT COUNT(DISTINCT r.member_id) at_risk FROM {s}.member_credit_ratings r
  JOIN (SELECT member_id, MAX(as_of_date) mx FROM {s}.member_credit_ratings GROUP BY member_id) m
    ON r.member_id=m.member_id AND r.as_of_date=m.mx
  WHERE r.next_review_due < CURRENT_DATE
)
SELECT
  ROUND(pos.total_advances_usd/1e9, 1) AS total_advances_bn,
  ROUND((pos.total_advances_usd + pos.total_ama_usd)/pos.consolidated_obligations_usd*100, 1) AS core_mission_ratio_pct,
  ROUND(COALESCE(pledge.ytd_disbursed,0)/1e6, 1) AS pledge_ytd_mm,
  dq.open_exceptions,
  atrisk.at_risk AS at_risk_members
FROM pos, pledge, dq, atrisk
"""


def overview_district(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {s}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
  GROUP BY member_id
)
SELECT m.charter_state AS state,
       COUNT(DISTINCT m.member_id) AS members,
       ROUND(SUM(COALESCE(a.advances,0))/1e9, 2) AS advances_bn
FROM {s}.members m LEFT JOIN adv a ON a.member_id=m.member_id
WHERE m.is_active
GROUP BY m.charter_state ORDER BY advances_bn DESC
"""


def overview_alerts(cfg: AppConfig) -> str:
    """Synthesize a cross-persona alert feed from several signal tables."""
    s = _s(cfg)
    return f"""
SELECT * FROM (
  SELECT 'CRO' AS persona, 'Rating cadence breach' AS title,
         CONCAT(m.member_name, ' overdue by ', CAST(DATEDIFF(CURRENT_DATE, r.next_review_due) AS STRING), ' days') AS detail,
         'high' AS severity, r.next_review_due AS event_date
  FROM {s}.member_credit_ratings r
  JOIN (SELECT member_id, MAX(as_of_date) mx FROM {s}.member_credit_ratings GROUP BY member_id) mm
    ON r.member_id=mm.member_id AND r.as_of_date=mm.mx
  JOIN {s}.members m ON m.member_id=r.member_id
  WHERE r.next_review_due < CURRENT_DATE
  ORDER BY r.next_review_due ASC LIMIT 3
)
UNION ALL SELECT * FROM (
  SELECT 'CIO', CONCAT(regulator, ' report exception'), CONCAT(report_name, ' - ', severity), 
         CASE WHEN severity='High' THEN 'high' ELSE 'medium' END, report_due_date
  FROM {s}.ops_data_quality_exceptions WHERE status='Open'
  ORDER BY report_due_date ASC LIMIT 3
)
UNION ALL SELECT * FROM (
  SELECT 'CIO', 'BI SLA miss', CONCAT(dashboard_name, ' (', bi_tool, ') ', CAST(actual_minutes-sla_minutes AS STRING), ' min over'),
         'medium', refresh_date
  FROM {s}.ops_bi_refresh WHERE sla_met_flag=false
  ORDER BY refresh_date DESC LIMIT 2
)
UNION ALL SELECT * FROM (
  SELECT 'Mission', 'AHP high-need project', CONCAT(project_name, ' - ', state),
         'low', CURRENT_DATE
  FROM {s}.ahp_applications WHERE tclp_high_need_flag=true AND status='Submitted'
  ORDER BY subsidy_requested_usd DESC LIMIT 2
)
ORDER BY event_date DESC
"""


# --------------------------------------------------------------------------- #
# CIO - Governance & Ops                                                       #
# --------------------------------------------------------------------------- #

def cio_dq_exceptions(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT e.report_name, e.regulator, s.system_name, s.instance_label, e.severity, e.report_due_date, e.description
FROM {s}.ops_data_quality_exceptions e
JOIN {s}.ops_source_systems s ON s.source_system_id=e.source_system_id
WHERE e.status='Open'
ORDER BY CASE e.severity WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, e.report_due_date
"""


def cio_bi_sla(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT bi_tool, COUNT(*) refreshes,
       SUM(CASE WHEN sla_met_flag THEN 0 ELSE 1 END) sla_misses,
       ROUND(AVG(actual_minutes), 0) avg_minutes
FROM {s}.ops_bi_refresh GROUP BY bi_tool ORDER BY sla_misses DESC
"""


def cio_dual_run_cost(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT DATE_FORMAT(cost_month, 'yyyy-MM') AS month, platform,
       ROUND(SUM(monthly_cost_usd)/1e3, 1) AS cost_k
FROM {s}.ops_pipeline_cost
GROUP BY DATE_FORMAT(cost_month,'yyyy-MM'), platform ORDER BY month
"""


def cio_model_backlog(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT model_name, model_type, owner, validation_status, validation_due_date,
       DATEDIFF(CURRENT_DATE, validation_due_date) AS days_overdue, touches_member_data_flag
FROM {s}.ops_model_inventory
WHERE validation_due_date < CURRENT_DATE OR validation_status <> 'Validated'
ORDER BY days_overdue DESC NULLS LAST
"""


def cio_access_oob(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT user_role, data_classification, COUNT(*) events,
       SUM(CASE WHEN in_policy_flag THEN 0 ELSE 1 END) out_of_policy
FROM {s}.ops_access_events
GROUP BY user_role, data_classification
HAVING out_of_policy > 0
ORDER BY out_of_policy DESC
"""


def cio_lineage(cfg: AppConfig, field: str) -> str:
    s = _s(cfg)
    safe = field.replace("'", "''")
    return f"""
SELECT l.field_name, sy.system_name, sy.instance_label, l.upstream_object, l.downstream_object, l.layer, l.submission_name
FROM {s}.ops_column_lineage l
LEFT JOIN {s}.ops_source_systems sy ON sy.source_system_id=l.source_system_id
WHERE l.field_name='{safe}'
ORDER BY l.layer
"""


def cio_lineage_fields(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"SELECT DISTINCT field_name FROM {s}.ops_column_lineage ORDER BY field_name"


# --------------------------------------------------------------------------- #
# CFO - Finance & Treasury                                                     #
# --------------------------------------------------------------------------- #

def cfo_advances_vs_forecast(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH actual AS (
  SELECT DATE_TRUNC('quarter', business_date) q, AVG(total_advances_usd) adv
  FROM {s}.bank_position_daily GROUP BY 1
),
fc AS (
  SELECT quarter_end_date, SUM(forecast_advances_usd) fc
  FROM {s}.advance_forecast_quarterly GROUP BY quarter_end_date
)
SELECT DATE_FORMAT(a.q, 'yyyy-MM') AS quarter,
       ROUND(a.adv/1e9, 2) AS actual_bn,
       ROUND(MAX(f.fc)/1e9, 2) AS forecast_bn
FROM actual a
LEFT JOIN fc f ON DATE_TRUNC('quarter', f.quarter_end_date)=a.q
GROUP BY a.q, a.adv ORDER BY a.q
"""


def cfo_core_mission_ratio(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT DATE_FORMAT(DATE_TRUNC('quarter', business_date), 'yyyy-MM') AS quarter,
       ROUND(AVG((total_advances_usd + total_ama_usd)/consolidated_obligations_usd)*100, 1) AS core_mission_ratio_pct
FROM {s}.bank_position_daily GROUP BY 1 ORDER BY 1
"""


def cfo_sofr_sensitivity(cfg: AppConfig, bps: int) -> str:
    """Approximate NII sensitivity to a parallel SOFR shift on floating advances."""
    s = _s(cfg)
    shift = bps / 10000.0
    return f"""
WITH latest AS (SELECT MAX(business_date) d FROM {s}.advance_daily_balances)
SELECT index_type,
       ROUND(SUM(outstanding_par_usd)/1e9, 2) AS balance_bn,
       ROUND(SUM(CASE WHEN index_type LIKE '%SOFR%' OR index_type='Floating' THEN outstanding_par_usd ELSE 0 END)*{shift}/1e6, 2) AS annual_nii_impact_mm
FROM {s}.advance_daily_balances WHERE business_date=(SELECT d FROM latest)
GROUP BY index_type ORDER BY balance_bn DESC
"""


def cfo_co_spreads(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT issue_date, co_type, spread_to_treasury_bps
FROM {s}.co_issuances
WHERE issue_date >= DATE_SUB(CURRENT_DATE, 90)
ORDER BY issue_date
"""


def cfo_mbs_unrealized(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT vintage_year, duration_bucket,
       ROUND(SUM(unrealized_gain_loss_usd)/1e6, 2) AS unrealized_mm,
       ROUND(SUM(market_value_usd)/1e6, 1) AS market_value_mm
FROM {s}.investment_holdings
GROUP BY vintage_year, duration_bucket ORDER BY vintage_year, duration_bucket
"""


# --------------------------------------------------------------------------- #
# CRO - Credit & Collateral                                                    #
# --------------------------------------------------------------------------- #

def cro_ratings_overdue(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH latest_adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {s}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
  GROUP BY member_id
),
latest_rating AS (
  SELECT r.* FROM {s}.member_credit_ratings r
  JOIN (SELECT member_id, MAX(as_of_date) mx FROM {s}.member_credit_ratings GROUP BY member_id) m
    ON r.member_id=m.member_id AND r.as_of_date=m.mx
)
SELECT m.member_id, m.member_name, m.member_type, lr.internal_rating, lr.prior_rating,
       lr.next_review_due, DATEDIFF(CURRENT_DATE, lr.next_review_due) AS days_overdue,
       ROUND(COALESCE(la.advances,0)/1e6, 1) AS advances_mm
FROM latest_rating lr
JOIN {s}.members m ON m.member_id=lr.member_id
LEFT JOIN latest_adv la ON la.member_id=lr.member_id
WHERE lr.next_review_due < CURRENT_DATE
ORDER BY la.advances DESC NULLS LAST LIMIT 15
"""


def cro_oc_cushion(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {s}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
  GROUP BY member_id
),
coll AS (SELECT member_id, SUM(lendable_value_usd) lendable FROM {s}.pledged_collateral GROUP BY member_id)
SELECT m.member_name, ROUND(coll.lendable/1e6, 1) lendable_mm,
       ROUND(COALESCE(adv.advances,0)/1e6, 1) advances_mm,
       ROUND((coll.lendable - COALESCE(adv.advances,0))/NULLIF(coll.lendable,0)*100, 1) AS oc_cushion_pct
FROM coll JOIN {s}.members m ON m.member_id=coll.member_id
LEFT JOIN adv ON adv.member_id=coll.member_id
WHERE coll.lendable > 0 AND COALESCE(adv.advances,0) > 0
ORDER BY oc_cushion_pct ASC LIMIT 15
"""


def cro_concentration(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {s}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
  GROUP BY member_id
), total AS (SELECT SUM(advances) t FROM adv)
SELECT m.member_name, m.member_type,
       ROUND(adv.advances/1e6, 1) AS advances_mm,
       ROUND(adv.advances/(SELECT t FROM total)*100, 1) AS pct_of_book
FROM adv JOIN {s}.members m ON m.member_id=adv.member_id
ORDER BY adv.advances DESC LIMIT 10
"""


def cro_mpf_delinquency(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT DATE_FORMAT(activity_month, 'yyyy-MM') AS month, delinquency_bucket,
       ROUND(SUM(upb_usd)/1e6, 1) AS upb_mm
FROM {s}.mpf_servicing_monthly
WHERE activity_month >= DATE_SUB(CURRENT_DATE, 365)
GROUP BY DATE_FORMAT(activity_month,'yyyy-MM'), delinquency_bucket
ORDER BY month
"""


def cro_early_warning_features(cfg: AppConfig, member_id: str | None = None) -> str:
    """Latest per-member feature snapshot for the Member Early-Warning model.

    Produces the exact feature columns the served model expects (member_type is
    mapped to a code inside the pyfunc), plus member identity fields the app uses
    to render the ranked watch board. Keep in lockstep with ml/train.py.
    """
    s = _s(cfg)
    member_filter = f"AND m.member_id = '{member_id}'" if member_id else ""
    return f"""
WITH latest_adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {s}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
  GROUP BY member_id
),
total AS (SELECT SUM(advances) t FROM latest_adv),
coll AS (SELECT member_id, SUM(lendable_value_usd) lendable FROM {s}.pledged_collateral GROUP BY member_id),
cr_latest AS (
  SELECT c.* FROM {s}.call_reports_quarterly c
  JOIN (SELECT member_id, MAX(quarter_end_date) mx
        FROM {s}.call_reports_quarterly GROUP BY member_id) mm
    ON c.member_id=mm.member_id AND c.quarter_end_date=mm.mx
),
rating_latest AS (
  SELECT r.* FROM {s}.member_credit_ratings r
  JOIN (SELECT member_id, MAX(as_of_date) mx
        FROM {s}.member_credit_ratings GROUP BY member_id) mm
    ON r.member_id=mm.member_id AND r.as_of_date=mm.mx
)
SELECT
  m.member_id, m.member_name, m.member_type, rl.internal_rating,
  CAST(SUBSTR(rl.internal_rating,1,1) AS INT) AS rating_num,
  ROUND(COALESCE(la.advances,0)/1e6, 1) AS advances_mm,
  crl.uninsured_deposit_ratio_pct,
  crl.brokered_deposit_growth_pct,
  ROUND(crl.unrealized_securities_loss_usd / NULLIF(crl.total_assets_usd,0) * 100, 3) AS aoci_to_assets_pct,
  crl.tier1_leverage_ratio_pct,
  DATEDIFF(CURRENT_DATE, rl.next_review_due) AS days_overdue,
  ROUND((coll.lendable - COALESCE(la.advances,0)) / NULLIF(coll.lendable,0) * 100, 2) AS oc_cushion_pct,
  ROUND(COALESCE(la.advances,0) / NULLIF(crl.total_assets_usd,0) * 100, 3) AS advances_to_assets_pct,
  ROUND(COALESCE(la.advances,0) / (SELECT t FROM total) * 100, 4) AS pct_of_book,
  ROUND(LN(GREATEST(m.asset_size_usd, 1)), 4) AS log_assets
FROM {s}.members m
JOIN cr_latest crl ON crl.member_id=m.member_id
JOIN rating_latest rl ON rl.member_id=m.member_id
LEFT JOIN latest_adv la ON la.member_id=m.member_id
LEFT JOIN coll ON coll.member_id=m.member_id
WHERE m.is_active {member_filter}
"""


# --------------------------------------------------------------------------- #
# CBO - Member & Products                                                      #
# --------------------------------------------------------------------------- #

def cbo_utilization(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT product,
       ROUND(SUM(outstanding_par_usd)/1e9, 2) AS balance_bn,
       COUNT(DISTINCT member_id) AS members
FROM {s}.advance_daily_balances
WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
GROUP BY product ORDER BY balance_bn DESC
"""


def cbo_unused_capacity(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
WITH adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {s}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {s}.advance_daily_balances)
  GROUP BY member_id
),
coll AS (SELECT member_id, SUM(lendable_value_usd) lendable FROM {s}.pledged_collateral GROUP BY member_id)
SELECT m.member_name, m.member_type, m.charter_state,
       ROUND((coll.lendable - COALESCE(adv.advances,0))/1e6, 1) AS unused_capacity_mm
FROM coll JOIN {s}.members m ON m.member_id=coll.member_id
LEFT JOIN adv ON adv.member_id=coll.member_id
ORDER BY unused_capacity_mm DESC LIMIT 15
"""


def cbo_mpf_leakage(cfg: AppConfig) -> str:
    """Members originating mortgages but selling to outlets other than MPF."""
    s = _s(cfg)
    return f"""
SELECT m.member_name, o.sold_to,
       ROUND(SUM(o.origination_volume_usd)/1e6, 1) AS volume_mm,
       SUM(o.loan_count) AS loans
FROM {s}.mortgage_originations o
JOIN {s}.members m ON m.member_id=o.member_id
WHERE o.sold_to <> 'MPF'
GROUP BY m.member_name, o.sold_to
ORDER BY volume_mm DESC LIMIT 15
"""


def cbo_eadvantage_lurkers(cfg: AppConfig) -> str:
    """Members active on eAdvantage but not transacting."""
    s = _s(cfg)
    return f"""
SELECT m.member_name, COUNT(*) sessions,
       SUM(CASE WHEN e.transacted_flag THEN 1 ELSE 0 END) transacted_sessions
FROM {s}.eadvantage_activity e
JOIN {s}.members m ON m.member_id=e.member_id
GROUP BY m.member_name
HAVING SUM(CASE WHEN e.transacted_flag THEN 1 ELSE 0 END)=0 AND COUNT(*) >= 3
ORDER BY sessions DESC LIMIT 15
"""


def cbo_prospects(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT institution_name, member_type, state,
       ROUND(asset_size_usd/1e9, 2) AS asset_bn,
       ROUND(mortgage_origination_volume_usd/1e6, 1) AS orig_mm,
       ROUND(similarity_score, 3) AS similarity
FROM {s}.eligible_nonmembers ORDER BY similarity_score DESC LIMIT 15
"""


# --------------------------------------------------------------------------- #
# Mission - $200M pledge & AHP                                                 #
# --------------------------------------------------------------------------- #

def mission_pledge(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT program,
       ROUND(SUM(committed_usd)/1e6, 2) AS committed_mm,
       ROUND(SUM(disbursed_usd)/1e6, 2) AS disbursed_mm
FROM {s}.pledge_activity
WHERE YEAR(activity_month)=YEAR(CURRENT_DATE)
GROUP BY program ORDER BY disbursed_mm DESC
"""


def mission_ahp_funnel(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT status, COUNT(*) applications, SUM(units_total) total_units,
       ROUND(SUM(subsidy_requested_usd)/1e6, 2) subsidy_mm,
       ROUND(AVG(subsidy_per_unit_usd), 0) avg_subsidy_per_unit
FROM {s}.ahp_applications GROUP BY status ORDER BY applications DESC
"""


def mission_subsidy_efficiency(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT project_type,
       ROUND(AVG(subsidy_per_unit_usd), 0) AS avg_subsidy_per_unit,
       SUM(units_total) AS units,
       COUNT(*) AS projects
FROM {s}.ahp_applications GROUP BY project_type ORDER BY avg_subsidy_per_unit
"""


def mission_units_by_tier(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT income_tier, rural_flag, SUM(units) AS units
FROM {s}.mission_units GROUP BY income_tier, rural_flag ORDER BY income_tier
"""


def mission_ai_sources(cfg: AppConfig) -> str:
    s = _s(cfg)
    return f"""
SELECT assistant_name, content_source, source_type, approver, governed_flag
FROM {s}.ops_ai_content_sources ORDER BY governed_flag DESC, assistant_name
"""
