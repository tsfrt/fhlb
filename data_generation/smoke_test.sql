-- Smoke-test queries for fhlb.des_moines: one representative persona question each.
-- Run against the SQL warehouse. These validate joins, planted patterns, and grain.

-- CRO (Joelyn Jensen-Marren): members past AB 2024-03 rating refresh cadence,
-- ranked by advances outstanding.
WITH latest_adv AS (
  SELECT member_id, SUM(outstanding_par_usd) AS advances_outstanding
  FROM fhlb.des_moines.advance_daily_balances
  WHERE business_date = (SELECT MAX(business_date) FROM fhlb.des_moines.advance_daily_balances)
  GROUP BY member_id
),
latest_rating AS (
  SELECT r.* FROM fhlb.des_moines.member_credit_ratings r
  JOIN (SELECT member_id, MAX(as_of_date) AS mx FROM fhlb.des_moines.member_credit_ratings GROUP BY member_id) m
    ON r.member_id = m.member_id AND r.as_of_date = m.mx
)
SELECT m.member_name, m.member_type, lr.internal_rating, lr.next_review_due,
       DATEDIFF(CURRENT_DATE, lr.next_review_due) AS days_overdue,
       la.advances_outstanding
FROM latest_rating lr
JOIN fhlb.des_moines.members m ON m.member_id = lr.member_id
LEFT JOIN latest_adv la ON la.member_id = lr.member_id
WHERE lr.next_review_due < CURRENT_DATE
ORDER BY la.advances_outstanding DESC NULLS LAST
LIMIT 10;

-- CFO (James Livingston): core mission asset ratio trend by quarter (advances + AMA)/CO.
SELECT DATE_TRUNC('quarter', business_date) AS quarter,
       ROUND(AVG(total_advances_usd)/1e9, 2) AS avg_advances_bn,
       ROUND(AVG(total_ama_usd)/1e9, 2) AS avg_ama_bn,
       ROUND(AVG(consolidated_obligations_usd)/1e9, 2) AS avg_co_bn,
       ROUND(AVG((total_advances_usd + total_ama_usd) / consolidated_obligations_usd) * 100, 2) AS core_mission_ratio_pct
FROM fhlb.des_moines.bank_position_daily
GROUP BY 1 ORDER BY 1;

-- CBO (Wil Osborn): members with the largest unused borrowing capacity
-- (lendable collateral minus advances outstanding).
WITH adv AS (
  SELECT member_id, SUM(outstanding_par_usd) AS advances
  FROM fhlb.des_moines.advance_daily_balances
  WHERE business_date = (SELECT MAX(business_date) FROM fhlb.des_moines.advance_daily_balances)
  GROUP BY member_id
),
coll AS (
  SELECT member_id, SUM(lendable_value_usd) AS lendable
  FROM fhlb.des_moines.pledged_collateral GROUP BY member_id
)
SELECT m.member_name, m.member_type,
       ROUND(coll.lendable/1e6, 1) AS lendable_mm,
       ROUND(COALESCE(adv.advances,0)/1e6, 1) AS advances_mm,
       ROUND((coll.lendable - COALESCE(adv.advances,0))/1e6, 1) AS unused_capacity_mm
FROM coll JOIN fhlb.des_moines.members m ON m.member_id = coll.member_id
LEFT JOIN adv ON adv.member_id = coll.member_id
ORDER BY unused_capacity_mm DESC LIMIT 10;

-- Mission (Livingston/Horton): AHP pipeline funnel with subsidy-per-unit distribution.
SELECT status,
       COUNT(*) AS applications,
       SUM(units_total) AS total_units,
       ROUND(SUM(subsidy_requested_usd)/1e6, 2) AS subsidy_mm,
       ROUND(AVG(subsidy_per_unit_usd), 0) AS avg_subsidy_per_unit
FROM fhlb.des_moines.ahp_applications
GROUP BY status
ORDER BY applications DESC;

-- CIO (Kevin Larkin): open FHFA report data-quality exceptions this quarter,
-- traced to the source SQL Server instance.
SELECT e.report_name, s.system_name, s.instance_label, e.severity, e.description
FROM fhlb.des_moines.ops_data_quality_exceptions e
JOIN fhlb.des_moines.ops_source_systems s ON s.source_system_id = e.source_system_id
WHERE e.status = 'Open'
ORDER BY e.severity, e.report_name;
