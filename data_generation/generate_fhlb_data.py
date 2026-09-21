"""
FHLB Des Moines synthetic demo dataset generator.

DEPRECATED (kept as a fallback): the data model is now populated by the Lakeflow
Spark Declarative Pipeline in ``pipeline/`` (a Databricks Asset Bundle). That
pipeline builds the same 38 tables as materialized views with a visual dependency
graph. This monolithic script is retained only as a reference / emergency
fallback and is no longer the source of truth. To (re)build the data, prefer:

    cd pipeline && databricks bundle deploy -p <profile> \\
        && databricks bundle run fhlb_data_pipeline --refresh-all -p <profile>

Approved plan: bls.fhlb -> retargeted to catalog `fhlb`, schema `des_moines`
(catalog `bls` was not creatable on this metastore; user chose the `fhlb` catalog).

All data is SYNTHETIC. Member names are fictional (district city + charter word).
Dollar magnitudes are scaled to be internally consistent and near public scale
(advances ~ $110B) but are not real FHLB Des Moines figures.

Generates ~35 raw tables (no pre-aggregations) mapped to the 50 persona questions
across CIO, CFO, CRO, CBO, and Mission audiences, for use with Databricks Genie.

Run:
  uv run --with "databricks-connect>=16.4,<17.4" --with faker --with pandas --with numpy \
      data_generation/generate_fhlb_data.py
"""

import datetime as dt
import numpy as np
import pandas as pd
from faker import Faker
from databricks.connect import DatabricksSession
from pyspark.sql import functions as F

PROFILE = "fevm-serverless-stable-blj52t"
CATALOG = "fhlb"
SCHEMA = "des_moines"
SEED = 42
TODAY = dt.date(2026, 8, 24)
HISTORY_START = TODAY - dt.timedelta(days=540)  # ~18 months

rng = np.random.default_rng(SEED)
fake = Faker()
Faker.seed(SEED)

# ---------------------------------------------------------------------------
# District geography (public): 13 states + 3 Pacific territories
# ---------------------------------------------------------------------------
STATES = ["AK", "HI", "ID", "IA", "MN", "MO", "MT", "ND", "OR", "SD", "UT", "WA", "WY", "AS", "GU", "MP"]
# Weight membership toward the larger-population core states.
STATE_W = np.array([3, 4, 5, 22, 20, 18, 4, 5, 12, 6, 6, 20, 2, 1, 1, 1], dtype=float)
STATE_W = STATE_W / STATE_W.sum()
STATE_CITY = {
    "AK": ["Anchorage", "Fairbanks"], "HI": ["Honolulu", "Hilo"], "ID": ["Boise", "Nampa"],
    "IA": ["Des Moines", "Cedar Rapids", "Davenport", "Ames"], "MN": ["Minneapolis", "Rochester", "Duluth"],
    "MO": ["St. Louis", "Kansas City", "Springfield"], "MT": ["Billings", "Missoula"],
    "ND": ["Fargo", "Bismarck"], "OR": ["Portland", "Eugene", "Salem"], "SD": ["Sioux Falls", "Rapid City"],
    "UT": ["Salt Lake City", "Provo"], "WA": ["Seattle", "Spokane", "Tacoma"], "WY": ["Cheyenne", "Casper"],
    "AS": ["Pago Pago"], "GU": ["Hagatna"], "MP": ["Saipan"],
}
CHARTER_WORDS = ["First", "Community", "Heritage", "Pioneer", "Summit", "Prairie", "Frontier", "Cornerstone",
                 "Legacy", "Meridian", "Vanguard", "Cascade", "Great Plains", "Northern", "Evergreen", "Liberty",
                 "Union", "Pinnacle", "Horizon", "Anchor"]

MEMBER_TYPES = ["Commercial Bank", "Credit Union", "Thrift", "Insurance Company", "CDFI"]
MEMBER_TYPE_W = np.array([0.44, 0.30, 0.10, 0.09, 0.07])

N_MEMBERS = 1250

# ---------------------------------------------------------------------------
# Spark session
# ---------------------------------------------------------------------------
spark = DatabricksSession.builder.profile(PROFILE).serverless(True).getOrCreate()
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA} "
          f"COMMENT 'Synthetic FHLB Des Moines demo data (fictional members and figures) for Genie'")

# metadata registry: table -> (table_comment, {column: comment}, [date_cols])
COMMENTS: dict[str, tuple[str, dict, list]] = {}


def write(df: pd.DataFrame, table: str, table_comment: str, col_comments: dict, date_cols=None):
    date_cols = date_cols or []
    sdf = spark.createDataFrame(df)
    for c in date_cols:
        sdf = sdf.withColumn(c, F.col(c).cast("date"))
    (sdf.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
        .saveAsTable(f"{CATALOG}.{SCHEMA}.{table}"))
    COMMENTS[table] = (table_comment, col_comments, date_cols)
    print(f"  wrote {CATALOG}.{SCHEMA}.{table}: {len(df):,} rows")


def apply_comments():
    print("Applying table and column comments...")
    for table, (tc, cc, _dc) in COMMENTS.items():
        fq = f"{CATALOG}.{SCHEMA}.{table}"
        spark.sql(f"COMMENT ON TABLE {fq} IS {sql_str(tc)}")
        for col, comment in cc.items():
            spark.sql(f"ALTER TABLE {fq} ALTER COLUMN {col} COMMENT {sql_str(comment)}")


def sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def daterange_days(n):
    return [HISTORY_START + dt.timedelta(days=int(x)) for x in range(n)]


def month_ends(start: dt.date, end: dt.date):
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        if m == 12:
            nd = dt.date(y, 12, 31)
        else:
            nd = dt.date(y, m + 1, 1) - dt.timedelta(days=1)
        out.append(nd)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def quarter_ends(n_back: int):
    # last n_back quarter-end dates up to most recent completed quarter
    qends = [dt.date(y, m, d) for y in range(2024, 2027) for (m, d) in [(3, 31), (6, 30), (9, 30), (12, 31)]]
    qends = [q for q in qends if q <= TODAY]
    return qends[-n_back:]


print(f"Target: {CATALOG}.{SCHEMA} | anchor date {TODAY} | history from {HISTORY_START}")

# ===========================================================================
# 1. MEMBERS (master)
# ===========================================================================
print("Generating members...")
states = rng.choice(STATES, size=N_MEMBERS, p=STATE_W)
mtypes = rng.choice(MEMBER_TYPES, size=N_MEMBERS, p=MEMBER_TYPE_W)
cities = [rng.choice(STATE_CITY[s]) for s in states]
names = []
seen = set()
for i in range(N_MEMBERS):
    suffix = {"Commercial Bank": "Bank", "Thrift": "Savings Bank", "Credit Union": "Credit Union",
              "Insurance Company": "Insurance", "CDFI": "Community Fund"}[mtypes[i]]
    # Shuffle charter words so we deterministically find a free name; fall back to a numeric suffix.
    order = rng.permutation(len(CHARTER_WORDS))
    nm = None
    for j in order:
        cand = f"{CHARTER_WORDS[j]} {suffix} of {cities[i]}"
        if cand not in seen:
            nm = cand
            break
    if nm is None:
        nm = f"{CHARTER_WORDS[order[0]]} {suffix} of {cities[i]} #{i}"
    seen.add(nm)
    names.append(nm)

# asset size (log-normal), insurance companies skew large
base_assets = np.exp(rng.normal(19.0, 1.3, N_MEMBERS))  # ~ tens/hundreds of millions
ins_mask = mtypes == "Insurance Company"
base_assets[ins_mask] *= rng.uniform(3, 12, ins_mask.sum())
# a handful of very large borrowers for concentration questions
big_idx = rng.choice(np.where(ins_mask)[0], size=min(6, ins_mask.sum()), replace=False)
base_assets[big_idx] *= rng.uniform(4, 8, len(big_idx))

is_cdfi = mtypes == "CDFI"
collateral_status = rng.choice(["Blanket Lien", "Specific Listing", "Delivery"], size=N_MEMBERS, p=[0.68, 0.22, 0.10])
membership_date = [TODAY - dt.timedelta(days=int(rng.integers(200, 9000))) for _ in range(N_MEMBERS)]
is_active = rng.random(N_MEMBERS) < 0.985
is_borrowing = rng.random(N_MEMBERS) < 0.58

member_ids = [f"MEM-{i:05d}" for i in range(1, N_MEMBERS + 1)]
members = pd.DataFrame({
    "member_id": member_ids,
    "member_name": names,
    "member_type": mtypes,
    "charter_state": states,
    "city": cities,
    "is_cdfi": is_cdfi,
    "asset_size_usd": np.round(base_assets, 2),
    "collateral_status": collateral_status,
    "membership_date": membership_date,
    "is_borrowing": is_borrowing,
    "is_active": is_active,
})
write(members, "members",
      "Synthetic FHLB Des Moines member institutions (fictional). One row per member.",
      {"member_id": "Unique member identifier (MEM-XXXXX).",
       "member_name": "Fictional member institution name.",
       "member_type": "Charter type: Commercial Bank, Credit Union, Thrift, Insurance Company, CDFI.",
       "charter_state": "Two-letter state or Pacific territory code in the FHLB Des Moines district.",
       "city": "Headquarters city.",
       "is_cdfi": "True if the member is a Community Development Financial Institution.",
       "asset_size_usd": "Total assets in USD (synthetic).",
       "collateral_status": "Collateral pledge status: Blanket Lien, Specific Listing, or Delivery.",
       "membership_date": "Date the institution joined the Bank.",
       "is_borrowing": "True if the member currently uses advances.",
       "is_active": "True if the membership is active."},
      date_cols=["membership_date"])

member_lookup = members.set_index("member_id")
borrowers = members.loc[members.is_borrowing & members.is_active, "member_id"].tolist()

# ===========================================================================
# 2. ELIGIBLE NONMEMBERS (prospects)
# ===========================================================================
print("Generating eligible_nonmembers...")
N_PROSPECT = 400
p_states = rng.choice(STATES, size=N_PROSPECT, p=STATE_W)
p_types = rng.choice(MEMBER_TYPES, size=N_PROSPECT, p=MEMBER_TYPE_W)
prospects = pd.DataFrame({
    "prospect_id": [f"PROS-{i:04d}" for i in range(1, N_PROSPECT + 1)],
    "institution_name": [f"{rng.choice(CHARTER_WORDS)} {rng.choice(['Bank','Credit Union','Savings Bank'])} of {rng.choice(STATE_CITY[s])}" for s in p_states],
    "member_type": p_types,
    "state": p_states,
    "asset_size_usd": np.round(np.exp(rng.normal(18.7, 1.2, N_PROSPECT)), 2),
    "mortgage_origination_volume_usd": np.round(np.exp(rng.normal(16.5, 1.1, N_PROSPECT)), 2),
    "similarity_score": np.round(rng.beta(2, 3, N_PROSPECT) * 100, 1),
})
write(prospects, "eligible_nonmembers",
      "Synthetic in-district institutions eligible for membership but not yet members (prospect list).",
      {"prospect_id": "Unique prospect identifier.",
       "institution_name": "Fictional institution name.",
       "member_type": "Charter type.",
       "state": "State or territory code.",
       "asset_size_usd": "Total assets in USD.",
       "mortgage_origination_volume_usd": "Annual mortgage origination volume in USD.",
       "similarity_score": "0-100 lookalike score vs the Bank's best-performing members (higher = better prospect)."})

# ===========================================================================
# 3. OPS SOURCE SYSTEMS (16 SQL Server instances + Fabric + feeds)
# ===========================================================================
print("Generating ops_source_systems...")
src_rows = []
for i in range(1, 17):
    src_rows.append((f"SRC-{i:03d}", f"SQLSVR-PROD-{i:02d}", "SQL Server", f"Instance {i:02d}", "Production"))
src_rows += [
    ("SRC-017", "FABRIC-LAKEHOUSE", "Microsoft Fabric", "Fabric-01", "Migration"),
    ("SRC-018", "MPF-PROVIDER-FEED", "External Feed", "FHLBank Chicago MPF Provider", "Production"),
    ("SRC-019", "FFIEC-CALLREPORT", "External Feed", "FFIEC Call Report", "Production"),
    ("SRC-020", "EADVANTAGE-APP", "Application", "eAdvantage member portal", "Production"),
]
source_systems = pd.DataFrame(src_rows, columns=["source_system_id", "system_name", "system_type", "instance_label", "environment"])
write(source_systems, "ops_source_systems",
      "Synthetic inventory of source systems feeding the data estate: 16 legacy SQL Server instances, a Microsoft Fabric build, and external feeds.",
      {"source_system_id": "Unique source system identifier.",
       "system_name": "System / instance name.",
       "system_type": "SQL Server, Microsoft Fabric, External Feed, or Application.",
       "instance_label": "Human-readable instance label.",
       "environment": "Production or Migration."})

# ===========================================================================
# 4. ADVANCE DAILY BALANCES
# ===========================================================================
print("Generating advance_daily_balances (this is the largest table)...")
N_ADV = min(460, len(borrowers))
adv_members = list(rng.choice(borrowers, size=N_ADV, replace=False))
days = daterange_days(541)
n_days = len(days)
day_arr = np.array(days)

PRODUCTS = ["Fixed Rate", "SOFR-Indexed", "CIP", "CICA"]
PRODUCT_W = np.array([0.55, 0.35, 0.06, 0.04])

rows = []
# recent surge window: last 30 days a subset of members ramp advances (thins OC cushion)
surge_members = set(rng.choice(adv_members, size=int(N_ADV * 0.18), replace=False))
for mid in adv_members:
    assets = float(member_lookup.loc[mid, "asset_size_usd"])
    base = max(2e6, assets * rng.uniform(0.05, 0.35))
    walk = np.cumsum(rng.normal(0, 0.01, n_days))
    level = base * np.exp(walk)
    if mid in surge_members:
        ramp = np.linspace(0, rng.uniform(0.4, 1.2), 30)
        level[-30:] = level[-30:] * (1 + ramp)
    product = rng.choice(PRODUCTS, p=PRODUCT_W)
    idx_type = "SOFR" if product == "SOFR-Indexed" else "Fixed"
    tenor_days = int(rng.choice([90, 180, 365, 730, 1095, 1825]))
    orig = TODAY - dt.timedelta(days=int(rng.integers(30, 500)))
    mat = orig + dt.timedelta(days=tenor_days)
    reprice = orig + dt.timedelta(days=int(rng.integers(30, 180))) if idx_type == "SOFR" else mat
    base_rate = rng.uniform(4.6, 5.6)
    # sample ~ every 3rd day to keep table ~250k rows but daily-grained near "today"
    for di in range(0, n_days, 3):
        par = float(level[di])
        rows.append((mid, day_arr[di], product, idx_type, round(par, 2),
                     round(par * base_rate / 100 / 365 * 3, 2), round(base_rate, 3),
                     orig, mat, reprice))
# ensure the final day is present for "as of this morning" questions
for mid in adv_members:
    pass

adv = pd.DataFrame(rows, columns=["member_id", "business_date", "product", "index_type",
                                  "outstanding_par_usd", "accrued_interest_usd", "rate_pct",
                                  "origination_date", "maturity_date", "repricing_date"])
adv["advance_id"] = ["ADV-" + str(i) for i in range(1, len(adv) + 1)]
adv = adv[["advance_id", "member_id", "business_date", "product", "index_type", "outstanding_par_usd",
           "accrued_interest_usd", "rate_pct", "origination_date", "maturity_date", "repricing_date"]]
write(adv, "advance_daily_balances",
      "Synthetic daily advance positions by member (sampled every ~3 days over 18 months). Raw balances; aggregate in queries.",
      {"advance_id": "Unique advance position row id.",
       "member_id": "FK to members.member_id.",
       "business_date": "Position date.",
       "product": "Advance product: Fixed Rate, SOFR-Indexed, CIP, CICA.",
       "index_type": "Rate index: SOFR or Fixed.",
       "outstanding_par_usd": "Outstanding par balance in USD.",
       "accrued_interest_usd": "Accrued interest in USD for the period.",
       "rate_pct": "Advance coupon rate in percent.",
       "origination_date": "Advance origination date.",
       "maturity_date": "Advance maturity date.",
       "repricing_date": "Next repricing date (equals maturity for fixed-rate)."},
      date_cols=["business_date", "origination_date", "maturity_date", "repricing_date"])

# ===========================================================================
# 5. PLEDGED COLLATERAL  + 6. COLLATERAL REVIEWS
# ===========================================================================
print("Generating pledged_collateral + collateral_reviews...")
COLL_TYPES = ["1-4 Family Mortgage", "Multifamily Mortgage", "Commercial Real Estate", "HELOC",
              "Agency MBS", "US Treasury/Agency", "Farm & Ag Real Estate", "Small Business"]
COLL_W = np.array([0.34, 0.14, 0.16, 0.06, 0.14, 0.08, 0.05, 0.03])
HAIRCUT = {"1-4 Family Mortgage": 0.24, "Multifamily Mortgage": 0.30, "Commercial Real Estate": 0.38,
           "HELOC": 0.42, "Agency MBS": 0.05, "US Treasury/Agency": 0.02, "Farm & Ag Real Estate": 0.35,
           "Small Business": 0.45}
lots = []
lot_id = 1
# most-recent latest advance par per member to size collateral so OC cushions are meaningful
latest = adv.sort_values("business_date").groupby("member_id").tail(1).set_index("member_id")["outstanding_par_usd"].to_dict()
for mid in adv_members:
    par = latest.get(mid, 5e6)
    # target lendable ~ 1.05-1.6x advances; surge members thinner
    mult = rng.uniform(1.02, 1.15) if mid in surge_members else rng.uniform(1.2, 1.7)
    target_lendable = par * mult
    n_lots = int(rng.integers(2, 6))
    for _ in range(n_lots):
        ct = rng.choice(COLL_TYPES, p=COLL_W)
        hc = HAIRCUT[ct] * rng.uniform(0.85, 1.15)
        lend = target_lendable / n_lots
        upb = lend / (1 - hc)
        lots.append((f"LOT-{lot_id:06d}", mid, TODAY, ct, round(upb, 2), round(lend, 2), round(hc * 100, 2)))
        lot_id += 1
pledged = pd.DataFrame(lots, columns=["lot_id", "member_id", "as_of_date", "collateral_type",
                                      "unpaid_principal_usd", "lendable_value_usd", "haircut_pct"])
write(pledged, "pledged_collateral",
      "Synthetic pledged collateral lots by member with lendable value and haircut. Unused capacity = lendable_value_usd minus advances outstanding.",
      {"lot_id": "Unique collateral lot id.",
       "member_id": "FK to members.member_id.",
       "as_of_date": "Collateral valuation date.",
       "collateral_type": "Collateral category (e.g., 1-4 Family Mortgage, Agency MBS).",
       "unpaid_principal_usd": "Unpaid principal balance / market value of the pledged lot in USD.",
       "lendable_value_usd": "Lendable (post-haircut) collateral value in USD.",
       "haircut_pct": "Applied collateral haircut in percent."},
      date_cols=["as_of_date"])

rev_rows = []
rid = 1
review_dates = month_ends(TODAY - dt.timedelta(days=365), TODAY)
for ct in COLL_TYPES:
    trend = rng.uniform(-0.5, 2.5)  # some types have rising exception rates
    for j, rdte in enumerate(review_dates):
        items = int(rng.integers(80, 400))
        base_rate = max(0.2, rng.uniform(0.5, 3.0) + trend * j / len(review_dates) * 4)
        exc = int(items * base_rate / 100)
        rev_rows.append((f"REV-{rid:05d}", rdte, ct, items, exc, round(exc / items * 100, 2)))
        rid += 1
coll_rev = pd.DataFrame(rev_rows, columns=["review_id", "review_date", "collateral_type", "items_reviewed",
                                           "exceptions_found", "exception_rate_pct"])
write(coll_rev, "collateral_reviews",
      "Synthetic collateral verification review results by collateral type and month. Rising exception rates suggest haircut changes.",
      {"review_id": "Unique review id.",
       "review_date": "Month-end review date.",
       "collateral_type": "Collateral category reviewed.",
       "items_reviewed": "Number of collateral items sampled.",
       "exceptions_found": "Number of exceptions identified.",
       "exception_rate_pct": "Exception rate in percent."},
      date_cols=["review_date"])

# ===========================================================================
# 7. LETTERS OF CREDIT
# ===========================================================================
print("Generating letters_of_credit...")
LOC_PURPOSE = ["Public Unit Deposit", "Housing/Community Development", "Asset-Liability Management", "Other"]
LOC_W = np.array([0.5, 0.22, 0.18, 0.10])
n_loc = 4200
loc_members = rng.choice(borrowers, size=n_loc)
issue = [TODAY - dt.timedelta(days=int(rng.integers(10, 700))) for _ in range(n_loc)]
loc = pd.DataFrame({
    "loc_id": [f"LOC-{i:05d}" for i in range(1, n_loc + 1)],
    "member_id": loc_members,
    "purpose": rng.choice(LOC_PURPOSE, size=n_loc, p=LOC_W),
    "notional_usd": np.round(np.exp(rng.normal(15.2, 1.0, n_loc)), 2),
    "issue_date": issue,
    "expiration_date": [d + dt.timedelta(days=int(rng.integers(180, 1460))) for d in issue],
})
loc["status"] = np.where(pd.to_datetime(loc["expiration_date"]) < pd.Timestamp(TODAY), "Expired", "Active")
write(loc, "letters_of_credit",
      "Synthetic standby letters of credit issued to members by purpose.",
      {"loc_id": "Unique letter-of-credit id.",
       "member_id": "FK to members.member_id.",
       "purpose": "LOC purpose (Public Unit Deposit, Housing/Community Development, ALM, Other).",
       "notional_usd": "Notional amount in USD.",
       "issue_date": "Issue date.",
       "expiration_date": "Expiration date.",
       "status": "Active or Expired."},
      date_cols=["issue_date", "expiration_date"])

# ===========================================================================
# 8. MEMBER CREDIT RATINGS (AB 2024-03 refresh cadence)
# ===========================================================================
print("Generating member_credit_ratings...")
RATINGS = ["1 - Strong", "2 - Satisfactory", "3 - Watch", "4 - Substandard", "5 - Doubtful"]
RATING_W = np.array([0.28, 0.44, 0.18, 0.08, 0.02])
rate_rows = []
rrid = 1
model_ids = ["MDL-CREDIT-01", "MDL-CREDIT-02"]
for mid in member_ids:
    n_hist = int(rng.integers(2, 6))
    cur = rng.choice(RATINGS, p=RATING_W)
    # cadence: strong members annually, weaker quarterly. Some overdue.
    cadence_days = 365 if cur in RATINGS[:2] else 180
    overdue = rng.random() < 0.16
    last_days = int(rng.integers(cadence_days + 30, cadence_days + 260)) if overdue else int(rng.integers(20, cadence_days - 20))
    as_of = TODAY - dt.timedelta(days=last_days)
    for h in range(n_hist):
        d = as_of - dt.timedelta(days=365 * (n_hist - 1 - h))
        prior = rng.choice(RATINGS, p=RATING_W)
        rate_rows.append((f"CR-{rrid:06d}", mid, d, cur if h == n_hist - 1 else prior, prior,
                          as_of + dt.timedelta(days=cadence_days) if h == n_hist - 1 else d + dt.timedelta(days=cadence_days),
                          cadence_days, rng.choice(model_ids)))
        rrid += 1
ratings = pd.DataFrame(rate_rows, columns=["rating_id", "member_id", "as_of_date", "internal_rating",
                                           "prior_rating", "next_review_due", "cadence_days", "rating_model_id"])
write(ratings, "member_credit_ratings",
      "Synthetic internal member credit rating history. next_review_due before today means past the AB 2024-03 refresh cadence.",
      {"rating_id": "Unique rating record id.",
       "member_id": "FK to members.member_id.",
       "as_of_date": "Effective date of the rating.",
       "internal_rating": "Internal credit rating grade (1 Strong to 5 Doubtful).",
       "prior_rating": "Prior rating grade.",
       "next_review_due": "Date the next rating refresh is due (AB 2024-03 cadence).",
       "cadence_days": "Required refresh cadence in days.",
       "rating_model_id": "FK to ops_model_inventory.model_id for the rating model used."},
      date_cols=["as_of_date", "next_review_due"])

# ===========================================================================
# 9. CALL REPORTS QUARTERLY (FFIEC-derived, planted deterioration)
# ===========================================================================
print("Generating call_reports_quarterly...")
qtrs = quarter_ends(6)
cr_rows = []
crid = 1
deteriorating = set(rng.choice(member_ids, size=int(N_MEMBERS * 0.12), replace=False))
for mid in member_ids:
    assets = float(member_lookup.loc[mid, "asset_size_usd"])
    base_unins = rng.uniform(8, 45)
    base_brok = rng.uniform(-2, 8)
    fed_use = rng.random() < 0.07
    for qi, q in enumerate(qtrs):
        drift = qi * (rng.uniform(2, 6) if mid in deteriorating else rng.uniform(-0.5, 0.5))
        unins = min(85, base_unins + drift)
        brok = base_brok + (drift * 0.4 if mid in deteriorating else rng.uniform(-1, 1))
        unreal = -abs(rng.normal(assets * 0.01, assets * 0.008)) * (1 + qi * 0.1 if mid in deteriorating else 1)
        cr_rows.append((f"CALL-{crid:06d}", mid, q, round(assets * rng.uniform(0.97, 1.03), 2),
                        round(unins, 2), round(brok, 2), round(unreal, 2),
                        bool(fed_use and qi >= len(qtrs) - 2),
                        round(rng.uniform(8, 13), 2)))
        crid += 1
call = pd.DataFrame(cr_rows, columns=["report_id", "member_id", "quarter_end_date", "total_assets_usd",
                                      "uninsured_deposit_ratio_pct", "brokered_deposit_growth_pct",
                                      "unrealized_securities_loss_usd", "fed_facility_usage_flag",
                                      "tier1_leverage_ratio_pct"])
write(call, "call_reports_quarterly",
      "Synthetic quarterly FFIEC call-report metrics per member. Some members show planted quarter-over-quarter deterioration.",
      {"report_id": "Unique call report row id.",
       "member_id": "FK to members.member_id.",
       "quarter_end_date": "Quarter-end date.",
       "total_assets_usd": "Total assets in USD.",
       "uninsured_deposit_ratio_pct": "Uninsured deposits as percent of total deposits.",
       "brokered_deposit_growth_pct": "Quarter-over-quarter brokered deposit growth percent.",
       "unrealized_securities_loss_usd": "Unrealized securities gain/loss in USD (negative = loss / AOCI).",
       "fed_facility_usage_flag": "True if the member shows discount window / Federal Reserve facility usage signals.",
       "tier1_leverage_ratio_pct": "Tier 1 leverage ratio percent."},
      date_cols=["quarter_end_date"])

# ===========================================================================
# 10. MORTGAGE ORIGINATIONS (find originators NOT delivering to MPF)
# ===========================================================================
print("Generating mortgage_originations...")
SOLD_TO = ["MPF", "Fannie Mae", "Freddie Mac", "Ginnie Mae", "Held in Portfolio"]
orig_members = [m for m in member_ids if member_lookup.loc[m, "member_type"] in ("Commercial Bank", "Thrift", "Credit Union")]
months = month_ends(HISTORY_START, TODAY)
mo_rows = []
moid = 1
# some members deliver to MPF, others clearly route to Fannie/Freddie instead
mpf_delivering = set(rng.choice(orig_members, size=int(len(orig_members) * 0.4), replace=False))
for mid in orig_members:
    if rng.random() < 0.25:
        continue  # not all originate meaningfully
    prefers = "MPF" if mid in mpf_delivering else rng.choice(["Fannie Mae", "Freddie Mac", "Ginnie Mae"])
    for mth in months:
        if rng.random() < 0.3:
            continue
        n_loans = int(rng.integers(3, 90))
        vol = n_loans * rng.uniform(180_000, 420_000)
        sold = prefers if rng.random() < 0.75 else rng.choice(SOLD_TO)
        mo_rows.append((f"ORIG-{moid:06d}", mid, mth, n_loans, round(vol, 2), sold))
        moid += 1
morig = pd.DataFrame(mo_rows, columns=["origination_id", "member_id", "origination_month", "loan_count",
                                       "origination_volume_usd", "sold_to"])
write(morig, "mortgage_originations",
      "Synthetic monthly mortgage origination activity by member, with secondary-market outlet. Members originating but with sold_to != 'MPF' are candidates not delivering into the MPF Program.",
      {"origination_id": "Unique origination record id.",
       "member_id": "FK to members.member_id.",
       "origination_month": "Month-end of origination activity.",
       "loan_count": "Number of loans originated.",
       "origination_volume_usd": "Origination dollar volume in USD.",
       "sold_to": "Secondary-market outlet: MPF, Fannie Mae, Freddie Mac, Ginnie Mae, or Held in Portfolio."},
      date_cols=["origination_month"])

# ===========================================================================
# 11. MPF LOANS (AMA book) + 12. MPF SERVICING MONTHLY
# ===========================================================================
print("Generating mpf_loans + mpf_servicing_monthly...")
pfis = list(mpf_delivering)
n_mpf = 25000
loan_members = rng.choice(pfis, size=n_mpf)
vintages = rng.choice(range(2016, 2027), size=n_mpf, p=np.array([2,3,4,5,6,8,10,14,18,16,14], dtype=float)/100)
occ = rng.choice(["Owner Occupied", "Second Home", "Investment"], size=n_mpf, p=[0.86, 0.06, 0.08])
low_income = rng.random(n_mpf) < 0.27
low_income_area = rng.random(n_mpf) < 0.19
upb = np.round(np.exp(rng.normal(12.3, 0.5, n_mpf)), 2)
mpf = pd.DataFrame({
    "loan_id": [f"MPF-{i:06d}" for i in range(1, n_mpf + 1)],
    "member_id": loan_members,
    "vintage_year": vintages,
    "current_upb_usd": upb,
    "occupancy": occ,
    "note_rate_pct": np.round(rng.uniform(3.0, 7.2, n_mpf), 3),
    "low_income_flag": low_income,
    "low_income_area_flag": low_income_area,
    "product": rng.choice(["MPF Original", "MPF Xtra", "MPF Direct"], size=n_mpf, p=[0.5, 0.35, 0.15]),
})
write(mpf, "mpf_loans",
      "Synthetic Mortgage Partnership Finance (MPF) / Acquired Member Asset loan book held by the Bank. Used for housing-goals low-income and low-income-area shares.",
      {"loan_id": "Unique MPF loan id.",
       "member_id": "FK to members.member_id (the Participating Financial Institution / PFI).",
       "vintage_year": "Origination vintage year.",
       "current_upb_usd": "Current unpaid principal balance in USD.",
       "occupancy": "Occupancy type.",
       "note_rate_pct": "Note rate percent.",
       "low_income_flag": "True if borrower income qualifies as low-income (FHFA housing goals).",
       "low_income_area_flag": "True if property is in a low-income area (FHFA housing goals).",
       "product": "MPF product variant."})

# servicing: monthly for a subset of loans over last 12 months
print("  building servicing history...")
serv_loans = mpf.sample(n=8000, random_state=SEED)
serv_months = month_ends(TODAY - dt.timedelta(days=365), TODAY)
DELINQ = ["Current", "30-59 Days", "60-89 Days", "90+ Days", "In Foreclosure"]
sv_rows = []
svid = 1
for _, ln in serv_loans.iterrows():
    # per-loan baseline delinquency propensity; some PFIs/vintages worse
    bad = 0.03 + (0.06 if ln.vintage_year <= 2018 else 0) + rng.uniform(0, 0.05)
    for mth in serv_months:
        r = rng.random()
        if r > bad:
            bucket = "Current"
        else:
            bucket = rng.choice(DELINQ[1:], p=[0.45, 0.25, 0.20, 0.10])
        hlc = bucket in ("90+ Days", "In Foreclosure") or (bucket == "60-89 Days" and rng.random() < 0.3)
        sv_rows.append((f"SVC-{svid:07d}", ln.loan_id, ln.member_id, mth, ln.vintage_year, bucket, bool(hlc),
                        round(float(ln.current_upb_usd) * rng.uniform(0.9, 1.0), 2)))
        svid += 1
serv = pd.DataFrame(sv_rows, columns=["servicing_id", "loan_id", "member_id", "activity_month", "vintage_year",
                                      "delinquency_bucket", "high_level_concern_flag", "upb_usd"])
write(serv, "mpf_servicing_monthly",
      "Synthetic monthly MPF servicing/delinquency data from the MPF Provider (FHLBank Chicago), by loan, PFI, and vintage.",
      {"servicing_id": "Unique servicing record id.",
       "loan_id": "FK to mpf_loans.loan_id.",
       "member_id": "FK to members.member_id (PFI).",
       "activity_month": "Servicing report month-end.",
       "vintage_year": "Loan vintage year.",
       "delinquency_bucket": "Delinquency status: Current, 30-59, 60-89, 90+ Days, In Foreclosure.",
       "high_level_concern_flag": "True if the loan is flagged High Level Concern.",
       "upb_usd": "Reported unpaid principal balance in USD."},
      date_cols=["activity_month"])

# ===========================================================================
# 13. INVESTMENT HOLDINGS (agency MBS) + 14. PREPAYMENT SPEEDS
# ===========================================================================
print("Generating investment_holdings + prepayment_speeds...")
n_hold = 2000
sec_type = rng.choice(["Agency MBS", "Agency CMO", "US Treasury", "Agency Debenture"], size=n_hold, p=[0.55, 0.2, 0.15, 0.1])
vint = rng.choice(range(2015, 2027), size=n_hold)
dur_bucket = rng.choice(["0-2y", "2-5y", "5-10y", "10y+"], size=n_hold, p=[0.25, 0.4, 0.25, 0.1])
book = np.round(np.exp(rng.normal(15.5, 0.7, n_hold)), 2)
# older/longer duration => larger unrealized losses in a higher-rate world
mkt_ratio = np.clip(rng.normal(0.965, 0.03, n_hold) - (2026 - vint) * 0.004 - np.isin(dur_bucket, ["5-10y", "10y+"]) * 0.02, 0.82, 1.05)
mkt = np.round(book * mkt_ratio, 2)
hold = pd.DataFrame({
    "holding_id": [f"INV-{i:05d}" for i in range(1, n_hold + 1)],
    "security_type": sec_type,
    "cusip": [fake.bothify("#####???#") for _ in range(n_hold)],
    "vintage_year": vint,
    "duration_bucket": dur_bucket,
    "book_value_usd": book,
    "market_value_usd": mkt,
    "unrealized_gain_loss_usd": np.round(mkt - book, 2),
})
write(hold, "investment_holdings",
      "Synthetic investment portfolio positions (agency MBS and related). Unrealized gain/loss by vintage and duration bucket.",
      {"holding_id": "Unique holding id.",
       "security_type": "Security type (Agency MBS, Agency CMO, US Treasury, Agency Debenture).",
       "cusip": "Synthetic CUSIP.",
       "vintage_year": "Vintage year.",
       "duration_bucket": "Duration bucket (0-2y, 2-5y, 5-10y, 10y+).",
       "book_value_usd": "Amortized book value in USD.",
       "market_value_usd": "Fair market value in USD.",
       "unrealized_gain_loss_usd": "Unrealized gain (positive) or loss (negative) in USD."})

pp_rows = []
ppid = 1
for portfolio in ["MPF Loans", "Agency MBS"]:
    fc = rng.uniform(6, 10)
    for mth in months:
        actual = max(2.0, fc + rng.normal(0, 2.2))
        pp_rows.append((f"PP-{ppid:05d}", portfolio, mth, round(actual, 2), round(fc, 2)))
        ppid += 1
prepay = pd.DataFrame(pp_rows, columns=["prepay_id", "portfolio", "activity_month", "actual_cpr_pct", "forecast_cpr_pct"])
write(prepay, "prepayment_speeds",
      "Synthetic actual vs forecast prepayment speeds (CPR) by portfolio and month.",
      {"prepay_id": "Unique row id.",
       "portfolio": "Portfolio: MPF Loans or Agency MBS.",
       "activity_month": "Month-end.",
       "actual_cpr_pct": "Actual conditional prepayment rate percent.",
       "forecast_cpr_pct": "Forecast/assumed CPR percent in the income forecast."},
      date_cols=["activity_month"])

# ===========================================================================
# 15. CO ISSUANCES + 16. MARKET RATES + ADVANCE PRICING + 17. BANK POSITION
# ===========================================================================
print("Generating co_issuances, market rates, advance pricing, bank_position_daily...")
n_co = 220
co_dates = [TODAY - dt.timedelta(days=int(rng.integers(0, 400))) for _ in range(n_co)]
co = pd.DataFrame({
    "issuance_id": [f"CO-{i:04d}" for i in range(1, n_co + 1)],
    "issue_date": co_dates,
    "co_type": rng.choice(["Discount Note", "Bond - Bullet", "Bond - Callable"], size=n_co, p=[0.5, 0.3, 0.2]),
    "tenor_months": rng.choice([1, 3, 6, 12, 24, 36, 60], size=n_co),
    "par_usd": np.round(rng.uniform(50e6, 2e9, n_co), 2),
    "spread_to_treasury_bps": np.round(rng.normal(8, 5, n_co), 1),
    "coupon_pct": np.round(rng.uniform(4.4, 5.4, n_co), 3),
})
write(co, "co_issuances",
      "Synthetic consolidated obligation (CO) issuances with spread to Treasuries.",
      {"issuance_id": "Unique issuance id.",
       "issue_date": "Issuance date.",
       "co_type": "Consolidated obligation type.",
       "tenor_months": "Tenor in months.",
       "par_usd": "Par amount issued in USD.",
       "spread_to_treasury_bps": "Issuance spread to Treasuries in basis points.",
       "coupon_pct": "Coupon rate percent."},
      date_cols=["issue_date"])

rate_days = daterange_days(541)
sofr = 4.85 + np.cumsum(rng.normal(0, 0.005, len(rate_days)))
mkt = pd.DataFrame({
    "business_date": rate_days,
    "sofr_pct": np.round(sofr, 3),
    "ust_3m_pct": np.round(sofr + rng.normal(-0.05, 0.02, len(rate_days)), 3),
    "ust_2y_pct": np.round(sofr - 0.35 + rng.normal(0, 0.03, len(rate_days)), 3),
    "ust_5y_pct": np.round(sofr - 0.25 + rng.normal(0, 0.03, len(rate_days)), 3),
    "ust_10y_pct": np.round(sofr - 0.05 + rng.normal(0, 0.03, len(rate_days)), 3),
})
write(mkt, "market_rates_daily",
      "Synthetic daily market rates: SOFR and Treasury curve points. Use for SOFR sensitivity and CO spread analysis.",
      {"business_date": "Rate date.",
       "sofr_pct": "Secured Overnight Financing Rate percent.",
       "ust_3m_pct": "US Treasury 3-month yield percent.",
       "ust_2y_pct": "US Treasury 2-year yield percent.",
       "ust_5y_pct": "US Treasury 5-year yield percent.",
       "ust_10y_pct": "US Treasury 10-year yield percent."},
      date_cols=["business_date"])

# advance pricing vs member funding alternatives (brokered deposits) by tenor
ap_rows = []
apid = 1
for d in daterange_days(541)[::7]:
    base = 4.85
    for tenor in [1, 3, 6, 12, 24, 36, 60]:
        adv_rate = base + tenor * 0.005 + rng.normal(0, 0.03)
        brok = adv_rate + rng.uniform(0.05, 0.35)  # brokered deposits typically pricier
        ap_rows.append((f"AP-{apid:05d}", d, tenor, round(adv_rate, 3), round(brok, 3)))
        apid += 1
ap = pd.DataFrame(ap_rows, columns=["price_id", "business_date", "tenor_months", "advance_rate_pct", "brokered_deposit_rate_pct"])
write(ap, "advance_pricing_daily",
      "Synthetic weekly advance pricing vs member funding alternatives (brokered deposits) by maturity point.",
      {"price_id": "Unique row id.",
       "business_date": "Pricing date.",
       "tenor_months": "Maturity point in months.",
       "advance_rate_pct": "Indicative advance rate percent.",
       "brokered_deposit_rate_pct": "Comparable brokered deposit rate percent members could obtain instead."},
      date_cols=["business_date"])

# bank position daily (bank-level totals) - tie advances to sum of member balances near today
bp_days = daterange_days(541)
total_adv0 = 110_000_000_000.0
adv_path = total_adv0 * np.exp(np.cumsum(rng.normal(0.0002, 0.004, len(bp_days))))
ama_path = 9_500_000_000 * np.exp(np.cumsum(rng.normal(0, 0.002, len(bp_days))))
co_out = (adv_path + ama_path) * rng.uniform(1.02, 1.06)
ni_mtd = []
for d in bp_days:
    ni_mtd.append(round(d.day * rng.uniform(1.4e6, 1.9e6), 2))
bank_pos = pd.DataFrame({
    "business_date": bp_days,
    "total_advances_usd": np.round(adv_path, 2),
    "total_ama_usd": np.round(ama_path, 2),
    "consolidated_obligations_usd": np.round(co_out, 2),
    "net_income_mtd_usd": ni_mtd,
})
write(bank_pos, "bank_position_daily",
      "Synthetic bank-level daily balance sheet snapshot. Core mission asset ratio = (total_advances_usd + total_ama_usd) / consolidated_obligations_usd.",
      {"business_date": "Position date.",
       "total_advances_usd": "Total advances outstanding in USD (bank-level).",
       "total_ama_usd": "Total Acquired Member Assets (MPF) in USD.",
       "consolidated_obligations_usd": "Consolidated obligations outstanding in USD.",
       "net_income_mtd_usd": "Month-to-date net income in USD."},
      date_cols=["business_date"])

# ===========================================================================
# 18. FORECASTS / FINANCIALS / VENDOR SPEND / CAPITAL PLAN
# ===========================================================================
print("Generating forecast + financials + vendor_spend + capital_plan...")
SEGMENTS = ["Commercial Bank", "Credit Union", "Thrift", "Insurance Company", "CDFI"]
fq_rows = []
for q in quarter_ends(6):
    for seg in SEGMENTS:
        fc = rng.uniform(6e9, 32e9)
        fq_rows.append((q, seg, round(fc, 2)))
fq = pd.DataFrame(fq_rows, columns=["quarter_end_date", "member_segment", "forecast_advances_usd"])
write(fq, "advance_forecast_quarterly",
      "Synthetic quarterly advance forecast by member segment. Compare to actual advance balances to compute variance.",
      {"quarter_end_date": "Quarter-end date.",
       "member_segment": "Member segment (by member_type).",
       "forecast_advances_usd": "Forecast advance balance in USD."},
      date_cols=["quarter_end_date"])

LINE_ITEMS = ["Net Interest Income", "Net Interest Spread", "Net Income", "Non-Interest Expense",
              "Contractual Services & Professional Fees", "AHP Assessment"]
fin_rows = []
finid = 1
for q in quarter_ends(4):
    for li in LINE_ITEMS:
        fcast = rng.uniform(2e7, 3e8) if li != "Net Interest Spread" else rng.uniform(0.35, 0.55)
        var = fcast * rng.normal(0, 0.08)
        fin_rows.append((f"FIN-{finid:04d}", q, li, round(fcast + var, 4), round(fcast, 4), round(var, 4)))
        finid += 1
fin = pd.DataFrame(fin_rows, columns=["fin_id", "quarter_end_date", "line_item", "actual_value", "forecast_value", "variance_value"])
write(fin, "financials_actual_vs_forecast",
      "Synthetic actual vs forecast financial line items by quarter (last 4 quarters). Spread is in percent; dollar lines in USD.",
      {"fin_id": "Unique row id.",
       "quarter_end_date": "Quarter-end date.",
       "line_item": "Financial line item name.",
       "actual_value": "Actual value (USD, or percent for Net Interest Spread).",
       "forecast_value": "Forecast value.",
       "variance_value": "Actual minus forecast."},
      date_cols=["quarter_end_date"])

VENDOR_CATS = ["Cloud Infrastructure", "Data & Analytics Software", "Legal", "Audit", "Consulting",
               "Managed Services", "Telecom", "Facilities"]
vs_rows = []
vsid = 1
for cat in VENDOR_CATS:
    growth = rng.uniform(-0.02, 0.06)
    plan = rng.uniform(1e5, 1.2e6)
    for i, mth in enumerate(month_ends(dt.date(TODAY.year, 1, 31), TODAY)):
        actual = plan * (1 + growth) ** i * rng.uniform(0.9, 1.15)
        vs_rows.append((f"VEN-{vsid:04d}", mth, cat, round(actual, 2), round(plan, 2)))
        vsid += 1
vs = pd.DataFrame(vs_rows, columns=["spend_id", "spend_month", "vendor_category", "actual_usd", "plan_usd"])
write(vs, "vendor_spend",
      "Synthetic vendor / contractual services spend by category and month vs plan (year to date).",
      {"spend_id": "Unique row id.",
       "spend_month": "Spend month-end.",
       "vendor_category": "Vendor category (e.g., Consulting, Cloud Infrastructure).",
       "actual_usd": "Actual spend in USD.",
       "plan_usd": "Planned spend in USD."},
      date_cols=["spend_month"])

cap_rows = []
for i, q in enumerate(quarter_ends(8)):
    target = 4.2e9
    re = target * (0.9 + i * 0.02) * rng.uniform(0.98, 1.03)
    cap_rows.append((q, round(re, 2), round(target, 2), round(rng.uniform(5.5e9, 6.5e9), 2)))
cap = pd.DataFrame(cap_rows, columns=["quarter_end_date", "retained_earnings_usd", "retained_earnings_target_usd", "activity_based_stock_usd"])
write(cap, "capital_plan",
      "Synthetic quarterly capital plan: retained earnings vs target and activity-based capital stock.",
      {"quarter_end_date": "Quarter-end date.",
       "retained_earnings_usd": "Retained earnings in USD.",
       "retained_earnings_target_usd": "Capital plan retained earnings target in USD.",
       "activity_based_stock_usd": "Activity-based capital stock in USD."},
      date_cols=["quarter_end_date"])

# ===========================================================================
# 19. AHP APPLICATIONS + 20. SET-ASIDE + 21. CIP/CICA + 22. MISSION UNITS + 23. PLEDGE
# ===========================================================================
print("Generating mission / AHP tables...")
AHP_STATUS = ["Received", "Scored", "Awarded", "Disbursed", "At Risk of Close", "De-obligated"]
AHP_STATUS_W = np.array([0.12, 0.15, 0.28, 0.30, 0.09, 0.06])
n_ahp = 420
ahp_states = rng.choice(STATES, size=n_ahp, p=STATE_W)
proj_type = rng.choice(["Rental", "Homeownership"], size=n_ahp, p=[0.68, 0.32])
units = rng.integers(4, 220, n_ahp)
subsidy_per_unit = np.round(rng.uniform(15_000, 150_000, n_ahp), 2)
subsidy = np.round(np.minimum(units * subsidy_per_unit, 3_000_000), 2)
ahp = pd.DataFrame({
    "application_id": [f"AHP-{i:04d}" for i in range(1, n_ahp + 1)],
    "member_id": rng.choice(member_ids, size=n_ahp),
    "project_name": [f"{fake.last_name()} {rng.choice(['Commons','Village','Terrace','Landing','Homes','Place','Crossing'])}" for _ in range(n_ahp)],
    "program": rng.choice(["Competitive AHP", "AHP General Fund"], size=n_ahp, p=[0.7, 0.3]),
    "project_type": proj_type,
    "status": rng.choice(AHP_STATUS, size=n_ahp, p=AHP_STATUS_W),
    "round_year": rng.choice([2024, 2025, 2026], size=n_ahp, p=[0.3, 0.4, 0.3]),
    "state": ahp_states,
    "units_total": units,
    "units_targeted": (units * rng.uniform(0.5, 1.0, n_ahp)).astype(int),
    "subsidy_requested_usd": subsidy,
    "subsidy_per_unit_usd": subsidy_per_unit,
    "tclp_high_need_flag": rng.random(n_ahp) < 0.4,
    "need_for_subsidy_ratio": np.round(rng.uniform(0.6, 1.4, n_ahp), 3),
    "score": np.round(rng.uniform(62, 79, n_ahp), 4),
})
write(ahp, "ahp_applications",
      "Synthetic Affordable Housing Program (AHP) applications through the funding pipeline. need_for_subsidy_ratio < 1 suggests overfunding; status tracks received->scored->awarded->disbursed with at-risk/de-obligated.",
      {"application_id": "Unique application id.",
       "member_id": "FK to members.member_id (sponsoring member).",
       "project_name": "Fictional project name.",
       "program": "Competitive AHP or AHP General Fund.",
       "project_type": "Rental or Homeownership.",
       "status": "Pipeline status: Received, Scored, Awarded, Disbursed, At Risk of Close, De-obligated.",
       "round_year": "Funding round year.",
       "state": "Project state/territory.",
       "units_total": "Total housing units in the project.",
       "units_targeted": "AHP-targeted (income-qualified) units.",
       "subsidy_requested_usd": "AHP subsidy requested in USD (capped at project max).",
       "subsidy_per_unit_usd": "Subsidy per targeted unit in USD (lower is more efficient).",
       "tclp_high_need_flag": "True if in a Targeted Community Lending Plan high-need geography.",
       "need_for_subsidy_ratio": "Need-for-subsidy analysis ratio for rentals (<1 = potentially overfunded).",
       "score": "AHP scoring result."},
      date_cols=[])

n_sa = 1200
sa = pd.DataFrame({
    "allocation_id": [f"SA-{i:05d}" for i in range(1, n_sa + 1)],
    "member_id": rng.choice(member_ids, size=n_sa),
    "product": rng.choice(["Home$tart (Down Payment Assistance)", "Native American Homeownership Initiative"], size=n_sa, p=[0.82, 0.18]),
    "program_year": rng.choice([2025, 2026], size=n_sa, p=[0.45, 0.55]),
    "allocated_usd": np.round(rng.uniform(5_000, 30_000, n_sa), 2),
})
sa["used_usd"] = np.round(sa["allocated_usd"] * rng.uniform(0, 1, n_sa), 2)
sa["expiration_date"] = [dt.date(int(y), 12, 31) for y in sa["program_year"]]
write(sa, "homeownership_setaside",
      "Synthetic homeownership set-aside / down payment assistance allocations by member. Unused = allocated_usd - used_usd; watch expiration_date.",
      {"allocation_id": "Unique allocation id.",
       "member_id": "FK to members.member_id.",
       "product": "Set-aside product (Home$tart or Native American Homeownership Initiative).",
       "program_year": "Program year.",
       "allocated_usd": "Allocated subsidy in USD.",
       "used_usd": "Used subsidy in USD.",
       "expiration_date": "Allocation expiration date."},
      date_cols=["expiration_date"])

n_cc = 2000
cc = pd.DataFrame({
    "activity_id": [f"CICA-{i:05d}" for i in range(1, n_cc + 1)],
    "member_id": rng.choice(member_ids, size=n_cc),
    "activity_date": [HISTORY_START + dt.timedelta(days=int(rng.integers(0, 540))) for _ in range(n_cc)],
    "program": rng.choice(["CIP", "CICA"], size=n_cc, p=[0.55, 0.45]),
    "purpose": rng.choice(["Housing", "Economic Development"], size=n_cc, p=[0.6, 0.4]),
    "amount_usd": np.round(np.exp(rng.normal(14.6, 0.9, n_cc)), 2),
    "units": rng.integers(0, 120, n_cc),
    "state": rng.choice(STATES, size=n_cc, p=STATE_W),
})
write(cc, "cip_cica_activity",
      "Synthetic Community Investment Program (CIP) and Community Investment Cash Advance (CICA) activity, split by housing vs economic development.",
      {"activity_id": "Unique activity id.",
       "member_id": "FK to members.member_id.",
       "activity_date": "Activity date.",
       "program": "CIP or CICA.",
       "purpose": "Housing or Economic Development.",
       "amount_usd": "Advance / investment amount in USD.",
       "units": "Housing units supported (if applicable).",
       "state": "State/territory."},
      date_cols=["activity_date"])

# mission units (FHFA mission-activity format): from AHP + set-aside grain
mu_rows = []
muid = 1
for _, a in ahp.iterrows():
    if a.status in ("Awarded", "Disbursed"):
        n = int(a.units_targeted)
        vli = int(n * rng.uniform(0.2, 0.6))
        mu_rows.append((f"MU-{muid:05d}", "AHP", a.state, "Very Low Income", bool(rng.random() < 0.35), vli))
        muid += 1
        mu_rows.append((f"MU-{muid:05d}", "AHP", a.state, "Low or Moderate Income", bool(rng.random() < 0.35), n - vli))
        muid += 1
mission_units = pd.DataFrame(mu_rows, columns=["mission_unit_id", "source_program", "state", "income_tier", "rural_flag", "units"])
write(mission_units, "mission_units",
      "Synthetic housing units supported this year by income tier and rural flag, in the format the FHFA mission-activities report uses.",
      {"mission_unit_id": "Unique row id.",
       "source_program": "Source program (AHP, set-aside).",
       "state": "State/territory.",
       "income_tier": "Income tier: Very Low Income or Low or Moderate Income.",
       "rural_flag": "True if rural.",
       "units": "Number of units."})

# pledge activity vs $200M
pl_rows = []
plid = 1
PROGRAMS = ["Competitive AHP", "Home$tart", "Native American Homeownership", "CIP/CICA", "Voluntary Contributions"]
for prog in PROGRAMS:
    for mth in month_ends(dt.date(TODAY.year, 1, 31), TODAY):
        for st in rng.choice(STATES, size=6, replace=False, p=STATE_W):
            committed = rng.uniform(50_000, 900_000)
            pl_rows.append((f"PLG-{plid:05d}", mth, prog, st, round(committed, 2), round(committed * rng.uniform(0.3, 0.95), 2)))
            plid += 1
pledge = pd.DataFrame(pl_rows, columns=["pledge_id", "activity_month", "program", "state", "committed_usd", "disbursed_usd"])
write(pledge, "pledge_activity",
      "Synthetic progress toward the $200M housing affordability pledge, by program, state, and month.",
      {"pledge_id": "Unique row id.",
       "activity_month": "Activity month-end.",
       "program": "Pledge program bucket.",
       "state": "State/territory.",
       "committed_usd": "Committed dollars in USD.",
       "disbursed_usd": "Disbursed dollars in USD."},
      date_cols=["activity_month"])

# ===========================================================================
# 24. EADVANTAGE ACTIVITY
# ===========================================================================
print("Generating eadvantage_activity...")
SCREENS = [("Advance Dashboard", "advance_daily_balances feed"), ("Collateral Summary", "pledged_collateral feed"),
           ("Rate Indications", "advance_pricing_daily feed"), ("Statements & Reports", "general_ledger feed"),
           ("MPF Delivery", "mpf_loans feed"), ("AHP & Grants", "ahp_applications feed")]
n_sess = 80000
sess_members = rng.choice(member_ids, size=n_sess)
# some members log in but do not transact in 90 days
non_transactors = set(rng.choice(member_ids, size=int(N_MEMBERS * 0.12), replace=False))
ea_rows = []
for i in range(n_sess):
    mid = sess_members[i]
    d = TODAY - dt.timedelta(days=int(rng.integers(0, 180)))
    screen, feed = SCREENS[rng.integers(0, len(SCREENS))]
    recent = (TODAY - d).days <= 90
    if mid in non_transactors:
        action = "Login" if rng.random() < 0.7 else "View"
    else:
        action = rng.choice(["Login", "View", "Transaction"], p=[0.4, 0.35, 0.25])
    transacted = action == "Transaction"
    ea_rows.append((f"SESS-{i+1:06d}", mid, d, screen, feed, action, bool(transacted)))
ea = pd.DataFrame(ea_rows, columns=["session_id", "member_id", "session_date", "screen", "feed_name", "action_type", "transacted_flag"])
write(ea, "eadvantage_activity",
      "Synthetic eAdvantage member-portal session activity. Identify members that log in but have not transacted in 90 days; feed_name shows what data feeds each screen.",
      {"session_id": "Unique session id.",
       "member_id": "FK to members.member_id.",
       "session_date": "Session date.",
       "screen": "eAdvantage screen viewed.",
       "feed_name": "Upstream data feed powering the screen.",
       "action_type": "Login, View, or Transaction.",
       "transacted_flag": "True if the session included a transaction."},
      date_cols=["session_date"])

# ===========================================================================
# 25-34. OPS / GOVERNANCE TABLES
# ===========================================================================
print("Generating ops / governance tables...")
FHFA_REPORTS = ["FHFA Call Report System Submission", "Advances & Collateral Quarterly (ACES)",
                "Member Financial Data Report", "AHP/CIP Mission Activities Report",
                "Capital Stock & Dividend Report", "Consolidated Obligations Report"]
# Reports are due within the CURRENT quarter so "due this quarter" questions return rows.
_cur_q = (TODAY.month - 1) // 3  # 0-based quarter index
_cur_q_start = dt.date(TODAY.year, _cur_q * 3 + 1, 1)
_cur_q_end = (dt.date(TODAY.year, _cur_q * 3 + 4, 1) - dt.timedelta(days=1)) if _cur_q < 3 else dt.date(TODAY.year, 12, 31)
_cur_q_span = (_cur_q_end - _cur_q_start).days
_cur_q_label = f"Q{_cur_q + 1} {TODAY.year}"
dq_rows = []
for i in range(1, 61):
    rep = rng.choice(FHFA_REPORTS)
    src = f"SRC-{rng.integers(1, 17):03d}"
    status = rng.choice(["Open", "Resolved"], p=[0.45, 0.55])
    due = _cur_q_start + dt.timedelta(days=int(rng.integers(0, _cur_q_span + 1)))
    dq_rows.append((f"DQ-{i:04d}", rep, "FHFA", due, _cur_q_label,
                    src, status, rng.choice(["High", "Medium", "Low"], p=[0.25, 0.5, 0.25]),
                    rng.choice(["Missing values", "Failed reconciliation", "Schema drift", "Late arrival", "Duplicate records"])))
dq = pd.DataFrame(dq_rows, columns=["exception_id", "report_name", "regulator", "report_due_date", "quarter",
                                    "source_system_id", "status", "severity", "description"])
write(dq, "ops_data_quality_exceptions",
      "Synthetic data-quality exceptions on regulatory reports, traced to a source system. Open exceptions on reports due this quarter are the CIO exam risk.",
      {"exception_id": "Unique exception id.",
       "report_name": "Regulatory report name.",
       "regulator": "Regulator (FHFA).",
       "report_due_date": "Report due date.",
       "quarter": "Reporting quarter label.",
       "source_system_id": "FK to ops_source_systems.source_system_id.",
       "status": "Open or Resolved.",
       "severity": "High, Medium, or Low.",
       "description": "Exception description."},
      date_cols=["report_due_date"])

lin_rows = [
    ("member_credit_rating", "SRC-019", "FFIEC Call Report ingest", "bronze.ffiec_call_raw", "Bronze", "FHFA Call Report System Submission"),
    ("member_credit_rating", "SRC-019", "bronze.ffiec_call_raw", "silver.member_financials", "Silver", "FHFA Call Report System Submission"),
    ("member_credit_rating", "SRC-002", "silver.member_financials", "gold.member_credit_ratings", "Gold", "FHFA Call Report System Submission"),
    ("member_credit_rating", "SRC-002", "gold.member_credit_ratings", "reg.fhfa_crs_submission", "Reporting", "FHFA Call Report System Submission"),
]
lineage = pd.DataFrame([(f"LIN-{i+1:03d}", *r) for i, r in enumerate(lin_rows)],
                       columns=["lineage_id", "field_name", "source_system_id", "upstream_object", "downstream_object", "layer", "submission_name"])
write(lineage, "ops_column_lineage",
      "Synthetic column-level lineage for the member credit rating field, from source ingestion to the FHFA-reported value.",
      {"lineage_id": "Unique edge id.",
       "field_name": "Tracked field name.",
       "source_system_id": "FK to ops_source_systems.source_system_id.",
       "upstream_object": "Upstream table/object.",
       "downstream_object": "Downstream table/object.",
       "layer": "Medallion / reporting layer.",
       "submission_name": "Regulatory submission the field flows into."})

DASH = [("Advances Executive View", "Qlik"), ("Collateral Risk Monitor", "Power BI"),
        ("Member 360", "Qlik"), ("Treasury Daily", "Power BI"), ("Mission & AHP", "Qlik"),
        ("Delinquency Trends", "Power BI")]
bi_rows = []
biid = 1
for name, tool in DASH:
    for d in [TODAY - dt.timedelta(days=x) for x in range(0, 30)]:
        sla = 60
        actual_late = rng.random() < 0.18
        actual = sla + (rng.integers(5, 90) if actual_late else -rng.integers(0, 40))
        bi_rows.append((f"BIR-{biid:05d}", name, tool, d, sla, int(actual), bool(actual <= sla),
                        f"extract_{name.lower().replace(' ','_')}"))
        biid += 1
bi = pd.DataFrame(bi_rows, columns=["refresh_id", "dashboard_name", "bi_tool", "refresh_date", "sla_minutes",
                                    "actual_minutes", "sla_met_flag", "extract_job"])
write(bi, "ops_bi_refresh",
      "Synthetic BI dashboard refresh log for Qlik and Power BI over the last 30 days, with SLA status and the extract job responsible.",
      {"refresh_id": "Unique refresh id.",
       "dashboard_name": "Dashboard name.",
       "bi_tool": "Qlik or Power BI.",
       "refresh_date": "Refresh date.",
       "sla_minutes": "Refresh SLA in minutes.",
       "actual_minutes": "Actual refresh duration in minutes.",
       "sla_met_flag": "True if refresh met SLA.",
       "extract_job": "Extract job that produced the data."},
      date_cols=["refresh_date"])

recon_metrics = ["Total Advances Outstanding", "Total Pledged Collateral", "Member Advance Balance",
                 "Consolidated Obligations", "AHP Assessment Accrual"]
mr_rows = []
for i, m in enumerate(recon_metrics):
    auth_val = rng.uniform(1e8, 1.2e11)
    qlik = auth_val * rng.uniform(0.999, 1.001)
    pbi = auth_val * rng.uniform(0.985, 1.015)
    mr_rows.append((f"REC-{i+1:03d}", m, round(qlik, 2), round(pbi, 2),
                    rng.choice(["gold.advances", "gold.collateral", "gold.bank_position"]), round(auth_val, 2),
                    TODAY, bool(abs(qlik - pbi) / auth_val > 0.005)))
mr = pd.DataFrame(mr_rows, columns=["reconciliation_id", "metric_name", "qlik_value", "powerbi_value",
                                    "authoritative_table", "authoritative_value", "as_of_date", "mismatch_flag"])
write(mr, "ops_metric_reconciliation",
      "Synthetic reconciliation of the same metric across Qlik and Power BI vs the authoritative Lakehouse table.",
      {"reconciliation_id": "Unique row id.",
       "metric_name": "Business metric name.",
       "qlik_value": "Value shown in Qlik.",
       "powerbi_value": "Value shown in Power BI.",
       "authoritative_table": "Authoritative source table.",
       "authoritative_value": "Authoritative value.",
       "as_of_date": "As-of date.",
       "mismatch_flag": "True if Qlik and Power BI disagree beyond tolerance."},
      date_cols=["as_of_date"])

ROLES = ["Credit Analyst", "Member Services", "Finance", "Executive", "External Auditor", "Data Engineer"]
ae_rows = []
for i in range(1, 1201):
    role = rng.choice(ROLES)
    cls = rng.choice(["Nonpublic Member Financial", "Public", "Internal"], p=[0.5, 0.2, 0.3])
    # accesses to nonpublic member data outside credit roles = out of policy
    in_policy = not (cls == "Nonpublic Member Financial" and role in ("Member Services", "Data Engineer") and rng.random() < 0.5)
    ae_rows.append((f"ACC-{i:05d}", fake.user_name(), TODAY - dt.timedelta(days=int(rng.integers(0, 90))),
                    rng.choice(["member_credit_ratings", "call_reports_quarterly", "pledged_collateral", "advance_daily_balances"]),
                    rng.choice(member_ids), cls, role, bool(in_policy)))
ae = pd.DataFrame(ae_rows, columns=["event_id", "user_name", "access_time", "data_object", "member_id",
                                    "data_classification", "user_role", "in_policy_flag"])
write(ae, "ops_access_events",
      "Synthetic access log over the last 90 days for nonpublic member financial data. in_policy_flag = False means access outside the role-based policy.",
      {"event_id": "Unique event id.",
       "user_name": "User who accessed the data.",
       "access_time": "Access date.",
       "data_object": "Data object accessed.",
       "member_id": "FK to members.member_id whose data was accessed.",
       "data_classification": "Data sensitivity classification.",
       "user_role": "Accessing user's role.",
       "in_policy_flag": "True if the access complied with role-based policy."},
      date_cols=["access_time"])

mdl_rows = []
MODELS = [("MDL-CREDIT-01", "Member Credit Rating Model", "Credit"), ("MDL-CREDIT-02", "Insurance Member Credit Model", "Credit"),
          ("MDL-COLL-01", "Collateral Valuation Model", "Collateral"), ("MDL-COLL-02", "Haircut Calibration Model", "Collateral"),
          ("MDL-PREPAY-01", "Prepayment Model", "Market"), ("MDL-AHP-01", "AHP Scoring Assist Model", "Mission"),
          ("MDL-AML-01", "Member Transaction Monitoring", "Compliance")]
for mid_, name, typ in MODELS:
    last_val = TODAY - dt.timedelta(days=int(rng.integers(120, 700)))
    due = last_val + dt.timedelta(days=365)
    mdl_rows.append((mid_, name, typ, fake.name(), last_val, due, True, "Overdue" if due < TODAY else "Current"))
mdl = pd.DataFrame(mdl_rows, columns=["model_id", "model_name", "model_type", "owner", "last_validation_date",
                                      "validation_due_date", "touches_member_data_flag", "validation_status"])
write(mdl, "ops_model_inventory",
      "Synthetic model inventory with last/next validation dates under FHFA model risk guidance. validation_due_date before today = past due.",
      {"model_id": "Unique model id.",
       "model_name": "Model name.",
       "model_type": "Credit, Collateral, Market, Mission, or Compliance.",
       "owner": "Model owner.",
       "last_validation_date": "Date of last validation.",
       "validation_due_date": "Next validation due date.",
       "touches_member_data_flag": "True if the model touches member data.",
       "validation_status": "Current or Overdue."},
      date_cols=["last_validation_date", "validation_due_date"])

REQ_TYPES = ["Member Credit File", "Collateral Position", "Advance Detail", "AHP Project File",
             "Model Documentation", "Data Lineage", "Access Report"]
er_rows = []
erid = 1
for cycle, mult in [("2025 Exam Cycle", 1.25), ("2026 Exam Cycle", 1.0)]:
    for rt in REQ_TYPES:
        for _ in range(int(rng.integers(4, 12))):
            recv = TODAY - dt.timedelta(days=int(rng.integers(30, 400)))
            base = {"Member Credit File": 3, "Collateral Position": 4, "Advance Detail": 2, "AHP Project File": 5,
                    "Model Documentation": 9, "Data Lineage": 11, "Access Report": 6}[rt]
            ta = max(1, int(rng.normal(base * mult, 2)))
            er_rows.append((f"REQ-{erid:04d}", cycle, rt, recv, recv + dt.timedelta(days=ta), ta))
            erid += 1
er = pd.DataFrame(er_rows, columns=["request_id", "exam_cycle", "request_type", "received_date", "fulfilled_date", "turnaround_days"])
write(er, "ops_examiner_requests",
      "Synthetic examiner data-request log across exam cycles, with turnaround days by request type. Compare cycles to show evidence-velocity improvement.",
      {"request_id": "Unique request id.",
       "exam_cycle": "Exam cycle label.",
       "request_type": "Type of examiner request.",
       "received_date": "Date the request was received.",
       "fulfilled_date": "Date the request was fulfilled.",
       "turnaround_days": "Turnaround time in days."},
      date_cols=["received_date", "fulfilled_date"])

pc_rows = []
pcid = 1
PIPELINES = [("Advances ETL", True), ("Collateral ETL", True), ("Member Financials ETL", True),
             ("MPF Servicing Load", False), ("Regulatory Reporting", True), ("AHP Pipeline", False),
             ("Investments Load", True)]
for name, dual in PIPELINES:
    for mth in month_ends(dt.date(TODAY.year, 1, 31), TODAY):
        for platform in (["SQL Server", "Microsoft Fabric"] if dual else ["SQL Server"]):
            cost = rng.uniform(8_000, 45_000) * (1.1 if platform == "Microsoft Fabric" else 1.0)
            pc_rows.append((f"PLC-{pcid:05d}", name, platform, mth, round(cost, 2), bool(dual)))
            pcid += 1
pc = pd.DataFrame(pc_rows, columns=["cost_id", "pipeline_name", "platform", "cost_month", "monthly_cost_usd", "is_dual_run_flag"])
write(pc, "ops_pipeline_cost",
      "Synthetic monthly pipeline run cost by platform. Pipelines with is_dual_run_flag run on both legacy SQL Server and Microsoft Fabric; sum both platforms for dual-run cost.",
      {"cost_id": "Unique row id.",
       "pipeline_name": "Pipeline name.",
       "platform": "SQL Server or Microsoft Fabric.",
       "cost_month": "Cost month-end.",
       "monthly_cost_usd": "Monthly run cost in USD.",
       "is_dual_run_flag": "True if the pipeline runs in parallel on both estates."},
      date_cols=["cost_month"])

gl_rows = []
for i, (screen, feed) in enumerate(SCREENS):
    last_rec = TODAY - dt.timedelta(days=int(rng.integers(0, 45)))
    gl_bal = rng.uniform(1e7, 5e10)
    feed_bal = gl_bal * rng.uniform(0.995, 1.005)
    gl_rows.append((f"GLR-{i+1:03d}", feed, screen, last_rec, round(gl_bal, 2), round(feed_bal, 2), round(feed_bal - gl_bal, 2)))
gl = pd.DataFrame(gl_rows, columns=["recon_id", "feed_name", "screen", "last_reconciled_date", "gl_balance_usd",
                                    "feed_balance_usd", "variance_usd"])
write(gl, "ops_gl_reconciliation",
      "Synthetic reconciliation of eAdvantage member-facing feeds against the general ledger, with last reconciled date.",
      {"recon_id": "Unique row id.",
       "feed_name": "Data feed powering an eAdvantage screen.",
       "screen": "eAdvantage screen.",
       "last_reconciled_date": "Date the feed was last reconciled to the GL.",
       "gl_balance_usd": "General ledger balance in USD.",
       "feed_balance_usd": "Feed balance in USD.",
       "variance_usd": "Feed minus GL in USD."},
      date_cols=["last_reconciled_date"])

ai_sources = [
    ("AHP Implementation Plan 2026", "Policy Document", "AHP Program Manager", True),
    ("Targeted Community Lending Plan", "Policy Document", "Community Investment Officer", True),
    ("AHP Scoring Criteria FAQ", "Knowledge Base", "AHP Program Manager", True),
    ("Member Outreach Emails", "Unstructured Email Archive", "Unapproved", False),
    ("Public FHFA Regulations", "External Web", "Compliance", True),
    ("Historical Award Data", "Structured Table", "Data Governance", True),
]
ai = pd.DataFrame([(f"AIS-{i+1:03d}", "Affordable Housing Virtual Assistant", src, typ, appr, bool(gov))
                   for i, (src, typ, appr, gov) in enumerate(ai_sources)],
                  columns=["source_id", "assistant_name", "content_source", "source_type", "approver", "governed_flag"])
write(ai, "ops_ai_content_sources",
      "Synthetic content-source registry for the Affordable Housing Virtual Assistant, with approver and governance status. governed_flag = False indicates an ungoverned source.",
      {"source_id": "Unique source id.",
       "assistant_name": "AI assistant name.",
       "content_source": "Content source the assistant draws on.",
       "source_type": "Type of content source.",
       "approver": "Who approved the source ('Unapproved' if none).",
       "governed_flag": "True if the source is governed/approved."})

# ===========================================================================
# Apply comments and finish
# ===========================================================================
apply_comments()
n_tables = spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").count()
print(f"DONE. {n_tables} tables in {CATALOG}.{SCHEMA}")
spark.stop()
