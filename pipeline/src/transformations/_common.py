"""Shared synthetic-data generators for the FHLB Des Moines Lakeflow pipeline.

This module contains the *pure* data-generation logic (numpy/pandas) that the
declarative pipeline transformation files wrap in ``@dp.table`` materialized
views. It is a faithful port of ``data_generation/generate_fhlb_data.py`` with
two changes:

  * generation is split into one deterministic function per table (each seeded
    independently), so a table can be rebuilt on its own inside the pipeline;
  * cross-table consistency is achieved by deterministic regeneration (a fixed
    seed per table means ``gen_members()`` always returns the same frame), while
    the transformation files add ``spark.read.table(...)`` left-semi joins so the
    Lakeflow graph renders the real dependency edges.

No Spark is imported here; ``finalize`` receives an already-built Spark
DataFrame. That keeps this module safe to import from every transformation file.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Anchors + district geography (kept identical to the original generator so the
# app's date-relative logic and Genie question set keep working).
# ---------------------------------------------------------------------------
TODAY = dt.date(2026, 8, 24)
HISTORY_START = TODAY - dt.timedelta(days=540)  # ~18 months

STATES = ["AK", "HI", "ID", "IA", "MN", "MO", "MT", "ND", "OR", "SD", "UT", "WA", "WY", "AS", "GU", "MP"]
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

_LAST_NAMES = ["Anderson", "Bennett", "Carlson", "Dawson", "Ellis", "Franklin", "Garrett", "Hoffman",
               "Iverson", "Jennings", "Klein", "Lawson", "Mercer", "Norris", "Ostrander", "Prescott",
               "Quinn", "Ramsey", "Sutton", "Thornton", "Underwood", "Vaughn", "Whitfield", "York"]


# ---------------------------------------------------------------------------
# Deterministic RNG + calendar helpers
# ---------------------------------------------------------------------------
def _seed(name: str) -> int:
    return int.from_bytes(hashlib.md5(name.encode()).digest()[:4], "big")


def rng_for(name: str) -> np.random.Generator:
    """A stable per-table numpy Generator (same seed every run)."""
    return np.random.default_rng(_seed(name))


def daterange_days(n: int):
    return [HISTORY_START + dt.timedelta(days=int(x)) for x in range(n)]


def month_ends(start: dt.date, end: dt.date):
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        nd = dt.date(y, 12, 31) if m == 12 else dt.date(y, m + 1, 1) - dt.timedelta(days=1)
        out.append(nd)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def quarter_ends(n_back: int):
    qends = [dt.date(y, m, d) for y in range(2024, 2027) for (m, d) in [(3, 31), (6, 30), (9, 30), (12, 31)]]
    qends = [q for q in qends if q <= TODAY]
    return qends[-n_back:]


def member_id_list():
    return [f"MEM-{i:05d}" for i in range(1, N_MEMBERS + 1)]


# ---------------------------------------------------------------------------
# 1. MEMBERS (master) — root of the graph
# ---------------------------------------------------------------------------
def gen_members() -> pd.DataFrame:
    rng = rng_for("members")
    states = rng.choice(STATES, size=N_MEMBERS, p=STATE_W)
    mtypes = rng.choice(MEMBER_TYPES, size=N_MEMBERS, p=MEMBER_TYPE_W)
    cities = [rng.choice(STATE_CITY[s]) for s in states]
    names, seen = [], set()
    for i in range(N_MEMBERS):
        suffix = {"Commercial Bank": "Bank", "Thrift": "Savings Bank", "Credit Union": "Credit Union",
                  "Insurance Company": "Insurance", "CDFI": "Community Fund"}[mtypes[i]]
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

    base_assets = np.exp(rng.normal(19.0, 1.3, N_MEMBERS))
    ins_mask = mtypes == "Insurance Company"
    base_assets[ins_mask] *= rng.uniform(3, 12, ins_mask.sum())
    big_idx = rng.choice(np.where(ins_mask)[0], size=min(6, int(ins_mask.sum())), replace=False)
    base_assets[big_idx] *= rng.uniform(4, 8, len(big_idx))

    return pd.DataFrame({
        "member_id": member_id_list(),
        "member_name": names,
        "member_type": mtypes,
        "charter_state": states,
        "city": cities,
        "is_cdfi": mtypes == "CDFI",
        "asset_size_usd": np.round(base_assets, 2),
        "collateral_status": rng.choice(["Blanket Lien", "Specific Listing", "Delivery"], size=N_MEMBERS, p=[0.68, 0.22, 0.10]),
        "membership_date": [TODAY - dt.timedelta(days=int(rng.integers(200, 9000))) for _ in range(N_MEMBERS)],
        "is_borrowing": rng.random(N_MEMBERS) < 0.58,
        "is_active": rng.random(N_MEMBERS) < 0.985,
    })


def _member_lookup():
    return gen_members().set_index("member_id")


def _borrowers():
    m = gen_members()
    return m.loc[m.is_borrowing & m.is_active, "member_id"].tolist()


# ---------------------------------------------------------------------------
# 2. ELIGIBLE NONMEMBERS
# ---------------------------------------------------------------------------
def gen_eligible_nonmembers() -> pd.DataFrame:
    rng = rng_for("eligible_nonmembers")
    n = 400
    p_states = rng.choice(STATES, size=n, p=STATE_W)
    return pd.DataFrame({
        "prospect_id": [f"PROS-{i:04d}" for i in range(1, n + 1)],
        "institution_name": [f"{rng.choice(CHARTER_WORDS)} {rng.choice(['Bank','Credit Union','Savings Bank'])} of {rng.choice(STATE_CITY[s])}" for s in p_states],
        "member_type": rng.choice(MEMBER_TYPES, size=n, p=MEMBER_TYPE_W),
        "state": p_states,
        "asset_size_usd": np.round(np.exp(rng.normal(18.7, 1.2, n)), 2),
        "mortgage_origination_volume_usd": np.round(np.exp(rng.normal(16.5, 1.1, n)), 2),
        "similarity_score": np.round(rng.beta(2, 3, n) * 100, 1),
    })


# ---------------------------------------------------------------------------
# 3. OPS SOURCE SYSTEMS
# ---------------------------------------------------------------------------
def gen_ops_source_systems() -> pd.DataFrame:
    rows = [(f"SRC-{i:03d}", f"SQLSVR-PROD-{i:02d}", "SQL Server", f"Instance {i:02d}", "Production") for i in range(1, 17)]
    rows += [
        ("SRC-017", "FABRIC-LAKEHOUSE", "Microsoft Fabric", "Fabric-01", "Migration"),
        ("SRC-018", "MPF-PROVIDER-FEED", "External Feed", "FHLBank Chicago MPF Provider", "Production"),
        ("SRC-019", "FFIEC-CALLREPORT", "External Feed", "FFIEC Call Report", "Production"),
        ("SRC-020", "EADVANTAGE-APP", "Application", "eAdvantage member portal", "Production"),
    ]
    return pd.DataFrame(rows, columns=["source_system_id", "system_name", "system_type", "instance_label", "environment"])


# ---------------------------------------------------------------------------
# 4. ADVANCE DAILY BALANCES (+ shared advance context)
# ---------------------------------------------------------------------------
PRODUCTS = ["Fixed Rate", "SOFR-Indexed", "CIP", "CICA"]
PRODUCT_W = np.array([0.55, 0.35, 0.06, 0.04])


def _advance_context():
    """Reproduce the advance member sample + surge set (shared by collateral)."""
    rng = rng_for("advance_daily_balances")
    borrowers = _borrowers()
    n_adv = min(460, len(borrowers))
    adv_members = list(rng.choice(borrowers, size=n_adv, replace=False))
    surge = set(rng.choice(adv_members, size=int(n_adv * 0.18), replace=False))
    return rng, adv_members, surge


def gen_advance_daily_balances() -> pd.DataFrame:
    rng, adv_members, surge = _advance_context()
    lookup = _member_lookup()
    days = daterange_days(541)
    n_days = len(days)
    day_arr = np.array(days)
    rows = []
    for mid in adv_members:
        assets = float(lookup.loc[mid, "asset_size_usd"])
        base = max(2e6, assets * rng.uniform(0.05, 0.35))
        level = base * np.exp(np.cumsum(rng.normal(0, 0.01, n_days)))
        if mid in surge:
            level[-30:] = level[-30:] * (1 + np.linspace(0, rng.uniform(0.4, 1.2), 30))
        product = rng.choice(PRODUCTS, p=PRODUCT_W)
        idx_type = "SOFR" if product == "SOFR-Indexed" else "Fixed"
        tenor_days = int(rng.choice([90, 180, 365, 730, 1095, 1825]))
        orig = TODAY - dt.timedelta(days=int(rng.integers(30, 500)))
        mat = orig + dt.timedelta(days=tenor_days)
        reprice = orig + dt.timedelta(days=int(rng.integers(30, 180))) if idx_type == "SOFR" else mat
        base_rate = rng.uniform(4.6, 5.6)
        for di in range(0, n_days, 3):
            par = float(level[di])
            rows.append((mid, day_arr[di], product, idx_type, round(par, 2),
                         round(par * base_rate / 100 / 365 * 3, 2), round(base_rate, 3), orig, mat, reprice))
    adv = pd.DataFrame(rows, columns=["member_id", "business_date", "product", "index_type", "outstanding_par_usd",
                                      "accrued_interest_usd", "rate_pct", "origination_date", "maturity_date", "repricing_date"])
    adv.insert(0, "advance_id", [f"ADV-{i}" for i in range(1, len(adv) + 1)])
    return adv


# ---------------------------------------------------------------------------
# 5/6. PLEDGED COLLATERAL + COLLATERAL REVIEWS
# ---------------------------------------------------------------------------
COLL_TYPES = ["1-4 Family Mortgage", "Multifamily Mortgage", "Commercial Real Estate", "HELOC",
              "Agency MBS", "US Treasury/Agency", "Farm & Ag Real Estate", "Small Business"]
COLL_W = np.array([0.34, 0.14, 0.16, 0.06, 0.14, 0.08, 0.05, 0.03])
HAIRCUT = {"1-4 Family Mortgage": 0.24, "Multifamily Mortgage": 0.30, "Commercial Real Estate": 0.38,
           "HELOC": 0.42, "Agency MBS": 0.05, "US Treasury/Agency": 0.02, "Farm & Ag Real Estate": 0.35,
           "Small Business": 0.45}


def gen_pledged_collateral() -> pd.DataFrame:
    _, adv_members, surge = _advance_context()
    lookup = _member_lookup()
    rng = rng_for("pledged_collateral")
    lots, lot_id = [], 1
    for mid in adv_members:
        assets = float(lookup.loc[mid, "asset_size_usd"])
        par = max(2e6, assets * rng.uniform(0.05, 0.35))
        mult = rng.uniform(1.02, 1.15) if mid in surge else rng.uniform(1.2, 1.7)
        target_lendable = par * mult
        n_lots = int(rng.integers(2, 6))
        for _ in range(n_lots):
            ct = rng.choice(COLL_TYPES, p=COLL_W)
            hc = HAIRCUT[ct] * rng.uniform(0.85, 1.15)
            lend = target_lendable / n_lots
            upb = lend / (1 - hc)
            lots.append((f"LOT-{lot_id:06d}", mid, TODAY, ct, round(upb, 2), round(lend, 2), round(hc * 100, 2)))
            lot_id += 1
    return pd.DataFrame(lots, columns=["lot_id", "member_id", "as_of_date", "collateral_type",
                                       "unpaid_principal_usd", "lendable_value_usd", "haircut_pct"])


def gen_collateral_reviews() -> pd.DataFrame:
    rng = rng_for("collateral_reviews")
    review_dates = month_ends(TODAY - dt.timedelta(days=365), TODAY)
    rows, rid = [], 1
    for ct in COLL_TYPES:
        trend = rng.uniform(-0.5, 2.5)
        for j, rdte in enumerate(review_dates):
            items = int(rng.integers(80, 400))
            base_rate = max(0.2, rng.uniform(0.5, 3.0) + trend * j / len(review_dates) * 4)
            exc = int(items * base_rate / 100)
            rows.append((f"REV-{rid:05d}", rdte, ct, items, exc, round(exc / items * 100, 2)))
            rid += 1
    return pd.DataFrame(rows, columns=["review_id", "review_date", "collateral_type", "items_reviewed",
                                       "exceptions_found", "exception_rate_pct"])


# ---------------------------------------------------------------------------
# 7. LETTERS OF CREDIT
# ---------------------------------------------------------------------------
def gen_letters_of_credit() -> pd.DataFrame:
    rng = rng_for("letters_of_credit")
    borrowers = _borrowers()
    n = 4200
    issue = [TODAY - dt.timedelta(days=int(rng.integers(10, 700))) for _ in range(n)]
    loc = pd.DataFrame({
        "loc_id": [f"LOC-{i:05d}" for i in range(1, n + 1)],
        "member_id": rng.choice(borrowers, size=n),
        "purpose": rng.choice(["Public Unit Deposit", "Housing/Community Development", "Asset-Liability Management", "Other"], size=n, p=[0.5, 0.22, 0.18, 0.10]),
        "notional_usd": np.round(np.exp(rng.normal(15.2, 1.0, n)), 2),
        "issue_date": issue,
        "expiration_date": [d + dt.timedelta(days=int(rng.integers(180, 1460))) for d in issue],
    })
    loc["status"] = np.where(pd.to_datetime(loc["expiration_date"]) < pd.Timestamp(TODAY), "Expired", "Active")
    return loc


# ---------------------------------------------------------------------------
# 8. MEMBER CREDIT RATINGS
# ---------------------------------------------------------------------------
RATINGS = ["1 - Strong", "2 - Satisfactory", "3 - Watch", "4 - Substandard", "5 - Doubtful"]
RATING_W = np.array([0.28, 0.44, 0.18, 0.08, 0.02])


def gen_member_credit_ratings() -> pd.DataFrame:
    rng = rng_for("member_credit_ratings")
    model_ids = ["MDL-CREDIT-01", "MDL-CREDIT-02"]
    rows, rrid = [], 1
    for mid in member_id_list():
        n_hist = int(rng.integers(2, 6))
        cur = rng.choice(RATINGS, p=RATING_W)
        cadence_days = 365 if cur in RATINGS[:2] else 180
        overdue = rng.random() < 0.16
        last_days = int(rng.integers(cadence_days + 30, cadence_days + 260)) if overdue else int(rng.integers(20, cadence_days - 20))
        as_of = TODAY - dt.timedelta(days=last_days)
        for h in range(n_hist):
            d = as_of - dt.timedelta(days=365 * (n_hist - 1 - h))
            prior = rng.choice(RATINGS, p=RATING_W)
            rows.append((f"CR-{rrid:06d}", mid, d, cur if h == n_hist - 1 else prior, prior,
                         as_of + dt.timedelta(days=cadence_days) if h == n_hist - 1 else d + dt.timedelta(days=cadence_days),
                         cadence_days, rng.choice(model_ids)))
            rrid += 1
    return pd.DataFrame(rows, columns=["rating_id", "member_id", "as_of_date", "internal_rating",
                                       "prior_rating", "next_review_due", "cadence_days", "rating_model_id"])


# ---------------------------------------------------------------------------
# 9. CALL REPORTS QUARTERLY
# ---------------------------------------------------------------------------
def gen_call_reports_quarterly() -> pd.DataFrame:
    rng = rng_for("call_reports_quarterly")
    lookup = _member_lookup()
    qtrs = quarter_ends(6)
    deteriorating = set(rng.choice(member_id_list(), size=int(N_MEMBERS * 0.12), replace=False))
    rows, crid = [], 1
    for mid in member_id_list():
        assets = float(lookup.loc[mid, "asset_size_usd"])
        base_unins = rng.uniform(8, 45)
        base_brok = rng.uniform(-2, 8)
        fed_use = rng.random() < 0.07
        for qi, q in enumerate(qtrs):
            drift = qi * (rng.uniform(2, 6) if mid in deteriorating else rng.uniform(-0.5, 0.5))
            unins = min(85, base_unins + drift)
            brok = base_brok + (drift * 0.4 if mid in deteriorating else rng.uniform(-1, 1))
            unreal = -abs(rng.normal(assets * 0.01, assets * 0.008)) * (1 + qi * 0.1 if mid in deteriorating else 1)
            rows.append((f"CALL-{crid:06d}", mid, q, round(assets * rng.uniform(0.97, 1.03), 2),
                         round(unins, 2), round(brok, 2), round(unreal, 2),
                         bool(fed_use and qi >= len(qtrs) - 2), round(rng.uniform(8, 13), 2)))
            crid += 1
    return pd.DataFrame(rows, columns=["report_id", "member_id", "quarter_end_date", "total_assets_usd",
                                       "uninsured_deposit_ratio_pct", "brokered_deposit_growth_pct",
                                       "unrealized_securities_loss_usd", "fed_facility_usage_flag", "tier1_leverage_ratio_pct"])


# ---------------------------------------------------------------------------
# 10/11/12. MORTGAGE ORIGINATIONS + MPF LOANS + SERVICING
# ---------------------------------------------------------------------------
SOLD_TO = ["MPF", "Fannie Mae", "Freddie Mac", "Ginnie Mae", "Held in Portfolio"]


def _mortgage_context():
    rng = rng_for("mortgage_originations")
    lookup = _member_lookup()
    orig_members = [m for m in member_id_list() if lookup.loc[m, "member_type"] in ("Commercial Bank", "Thrift", "Credit Union")]
    mpf_delivering = set(rng.choice(orig_members, size=int(len(orig_members) * 0.4), replace=False))
    return rng, orig_members, mpf_delivering


def gen_mortgage_originations() -> pd.DataFrame:
    rng, orig_members, mpf_delivering = _mortgage_context()
    months = month_ends(HISTORY_START, TODAY)
    rows, moid = [], 1
    for mid in orig_members:
        if rng.random() < 0.25:
            continue
        prefers = "MPF" if mid in mpf_delivering else rng.choice(["Fannie Mae", "Freddie Mac", "Ginnie Mae"])
        for mth in months:
            if rng.random() < 0.3:
                continue
            n_loans = int(rng.integers(3, 90))
            vol = n_loans * rng.uniform(180_000, 420_000)
            sold = prefers if rng.random() < 0.75 else rng.choice(SOLD_TO)
            rows.append((f"ORIG-{moid:06d}", mid, mth, n_loans, round(vol, 2), sold))
            moid += 1
    return pd.DataFrame(rows, columns=["origination_id", "member_id", "origination_month", "loan_count",
                                       "origination_volume_usd", "sold_to"])


def gen_mpf_loans() -> pd.DataFrame:
    _, _, mpf_delivering = _mortgage_context()
    rng = rng_for("mpf_loans")
    pfis = list(mpf_delivering)
    n = 25000
    return pd.DataFrame({
        "loan_id": [f"MPF-{i:06d}" for i in range(1, n + 1)],
        "member_id": rng.choice(pfis, size=n),
        "vintage_year": rng.choice(range(2016, 2027), size=n, p=np.array([2, 3, 4, 5, 6, 8, 10, 14, 18, 16, 14], dtype=float) / 100),
        "current_upb_usd": np.round(np.exp(rng.normal(12.3, 0.5, n)), 2),
        "occupancy": rng.choice(["Owner Occupied", "Second Home", "Investment"], size=n, p=[0.86, 0.06, 0.08]),
        "note_rate_pct": np.round(rng.uniform(3.0, 7.2, n), 3),
        "low_income_flag": rng.random(n) < 0.27,
        "low_income_area_flag": rng.random(n) < 0.19,
        "product": rng.choice(["MPF Original", "MPF Xtra", "MPF Direct"], size=n, p=[0.5, 0.35, 0.15]),
    })


def gen_mpf_servicing_monthly() -> pd.DataFrame:
    loans = gen_mpf_loans().sample(n=8000, random_state=_seed("mpf_servicing_monthly"))
    rng = rng_for("mpf_servicing_monthly")
    serv_months = month_ends(TODAY - dt.timedelta(days=365), TODAY)
    DELINQ = ["Current", "30-59 Days", "60-89 Days", "90+ Days", "In Foreclosure"]
    rows, svid = [], 1
    for _, ln in loans.iterrows():
        bad = 0.03 + (0.06 if ln.vintage_year <= 2018 else 0) + rng.uniform(0, 0.05)
        for mth in serv_months:
            bucket = "Current" if rng.random() > bad else rng.choice(DELINQ[1:], p=[0.45, 0.25, 0.20, 0.10])
            hlc = bucket in ("90+ Days", "In Foreclosure") or (bucket == "60-89 Days" and rng.random() < 0.3)
            rows.append((f"SVC-{svid:07d}", ln.loan_id, ln.member_id, mth, ln.vintage_year, bucket, bool(hlc),
                         round(float(ln.current_upb_usd) * rng.uniform(0.9, 1.0), 2)))
            svid += 1
    return pd.DataFrame(rows, columns=["servicing_id", "loan_id", "member_id", "activity_month", "vintage_year",
                                       "delinquency_bucket", "high_level_concern_flag", "upb_usd"])


# ---------------------------------------------------------------------------
# 13/14. INVESTMENT HOLDINGS + PREPAYMENT SPEEDS
# ---------------------------------------------------------------------------
def gen_investment_holdings() -> pd.DataFrame:
    rng = rng_for("investment_holdings")
    n = 2000
    sec_type = rng.choice(["Agency MBS", "Agency CMO", "US Treasury", "Agency Debenture"], size=n, p=[0.55, 0.2, 0.15, 0.1])
    vint = rng.choice(range(2015, 2027), size=n)
    dur_bucket = rng.choice(["0-2y", "2-5y", "5-10y", "10y+"], size=n, p=[0.25, 0.4, 0.25, 0.1])
    book = np.round(np.exp(rng.normal(15.5, 0.7, n)), 2)
    mkt_ratio = np.clip(rng.normal(0.965, 0.03, n) - (2026 - vint) * 0.004 - np.isin(dur_bucket, ["5-10y", "10y+"]) * 0.02, 0.82, 1.05)
    mkt = np.round(book * mkt_ratio, 2)
    _CUSIP_CH = np.array(list("ABCDEFGHJKLMNPQRSTUVWXYZ"))
    cusips = ["".join(rng.integers(0, 10, 5).astype(str)) + "".join(rng.choice(_CUSIP_CH, 3)) + str(int(rng.integers(0, 10))) for _ in range(n)]
    return pd.DataFrame({
        "holding_id": [f"INV-{i:05d}" for i in range(1, n + 1)],
        "security_type": sec_type,
        "cusip": cusips,
        "vintage_year": vint,
        "duration_bucket": dur_bucket,
        "book_value_usd": book,
        "market_value_usd": mkt,
        "unrealized_gain_loss_usd": np.round(mkt - book, 2),
    })


def gen_prepayment_speeds() -> pd.DataFrame:
    rng = rng_for("prepayment_speeds")
    months = month_ends(HISTORY_START, TODAY)
    rows, ppid = [], 1
    for portfolio in ["MPF Loans", "Agency MBS"]:
        fc = rng.uniform(6, 10)
        for mth in months:
            actual = max(2.0, fc + rng.normal(0, 2.2))
            rows.append((f"PP-{ppid:05d}", portfolio, mth, round(actual, 2), round(fc, 2)))
            ppid += 1
    return pd.DataFrame(rows, columns=["prepay_id", "portfolio", "activity_month", "actual_cpr_pct", "forecast_cpr_pct"])


# ---------------------------------------------------------------------------
# 15/16/17. CO ISSUANCES + MARKET RATES + ADVANCE PRICING + BANK POSITION
# ---------------------------------------------------------------------------
def gen_co_issuances() -> pd.DataFrame:
    rng = rng_for("co_issuances")
    n = 220
    return pd.DataFrame({
        "issuance_id": [f"CO-{i:04d}" for i in range(1, n + 1)],
        "issue_date": [TODAY - dt.timedelta(days=int(rng.integers(0, 400))) for _ in range(n)],
        "co_type": rng.choice(["Discount Note", "Bond - Bullet", "Bond - Callable"], size=n, p=[0.5, 0.3, 0.2]),
        "tenor_months": rng.choice([1, 3, 6, 12, 24, 36, 60], size=n),
        "par_usd": np.round(rng.uniform(50e6, 2e9, n), 2),
        "spread_to_treasury_bps": np.round(rng.normal(8, 5, n), 1),
        "coupon_pct": np.round(rng.uniform(4.4, 5.4, n), 3),
    })


def gen_market_rates_daily() -> pd.DataFrame:
    rng = rng_for("market_rates_daily")
    rate_days = daterange_days(541)
    sofr = 4.85 + np.cumsum(rng.normal(0, 0.005, len(rate_days)))
    return pd.DataFrame({
        "business_date": rate_days,
        "sofr_pct": np.round(sofr, 3),
        "ust_3m_pct": np.round(sofr + rng.normal(-0.05, 0.02, len(rate_days)), 3),
        "ust_2y_pct": np.round(sofr - 0.35 + rng.normal(0, 0.03, len(rate_days)), 3),
        "ust_5y_pct": np.round(sofr - 0.25 + rng.normal(0, 0.03, len(rate_days)), 3),
        "ust_10y_pct": np.round(sofr - 0.05 + rng.normal(0, 0.03, len(rate_days)), 3),
    })


def gen_advance_pricing_daily() -> pd.DataFrame:
    rng = rng_for("advance_pricing_daily")
    rows, apid = [], 1
    for d in daterange_days(541)[::7]:
        base = 4.85
        for tenor in [1, 3, 6, 12, 24, 36, 60]:
            adv_rate = base + tenor * 0.005 + rng.normal(0, 0.03)
            brok = adv_rate + rng.uniform(0.05, 0.35)
            rows.append((f"AP-{apid:05d}", d, tenor, round(adv_rate, 3), round(brok, 3)))
            apid += 1
    return pd.DataFrame(rows, columns=["price_id", "business_date", "tenor_months", "advance_rate_pct", "brokered_deposit_rate_pct"])


def gen_bank_position_daily() -> pd.DataFrame:
    rng = rng_for("bank_position_daily")
    bp_days = daterange_days(541)
    adv_path = 110_000_000_000.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.004, len(bp_days))))
    ama_path = 9_500_000_000 * np.exp(np.cumsum(rng.normal(0, 0.002, len(bp_days))))
    co_out = (adv_path + ama_path) * rng.uniform(1.02, 1.06)
    ni_mtd = [round(d.day * rng.uniform(1.4e6, 1.9e6), 2) for d in bp_days]
    return pd.DataFrame({
        "business_date": bp_days,
        "total_advances_usd": np.round(adv_path, 2),
        "total_ama_usd": np.round(ama_path, 2),
        "consolidated_obligations_usd": np.round(co_out, 2),
        "net_income_mtd_usd": ni_mtd,
    })


# ---------------------------------------------------------------------------
# 18. FORECASTS / FINANCIALS / VENDOR SPEND / CAPITAL PLAN
# ---------------------------------------------------------------------------
def gen_advance_forecast_quarterly() -> pd.DataFrame:
    rng = rng_for("advance_forecast_quarterly")
    rows = []
    for q in quarter_ends(6):
        for seg in MEMBER_TYPES:
            rows.append((q, seg, round(rng.uniform(6e9, 32e9), 2)))
    return pd.DataFrame(rows, columns=["quarter_end_date", "member_segment", "forecast_advances_usd"])


def gen_financials_actual_vs_forecast() -> pd.DataFrame:
    rng = rng_for("financials_actual_vs_forecast")
    line_items = ["Net Interest Income", "Net Interest Spread", "Net Income", "Non-Interest Expense",
                  "Contractual Services & Professional Fees", "AHP Assessment"]
    rows, finid = [], 1
    for q in quarter_ends(4):
        for li in line_items:
            fcast = rng.uniform(2e7, 3e8) if li != "Net Interest Spread" else rng.uniform(0.35, 0.55)
            var = fcast * rng.normal(0, 0.08)
            rows.append((f"FIN-{finid:04d}", q, li, round(fcast + var, 4), round(fcast, 4), round(var, 4)))
            finid += 1
    return pd.DataFrame(rows, columns=["fin_id", "quarter_end_date", "line_item", "actual_value", "forecast_value", "variance_value"])


def gen_vendor_spend() -> pd.DataFrame:
    rng = rng_for("vendor_spend")
    cats = ["Cloud Infrastructure", "Data & Analytics Software", "Legal", "Audit", "Consulting",
            "Managed Services", "Telecom", "Facilities"]
    rows, vsid = [], 1
    for cat in cats:
        growth = rng.uniform(-0.02, 0.06)
        plan = rng.uniform(1e5, 1.2e6)
        for i, mth in enumerate(month_ends(dt.date(TODAY.year, 1, 31), TODAY)):
            actual = plan * (1 + growth) ** i * rng.uniform(0.9, 1.15)
            rows.append((f"VEN-{vsid:04d}", mth, cat, round(actual, 2), round(plan, 2)))
            vsid += 1
    return pd.DataFrame(rows, columns=["spend_id", "spend_month", "vendor_category", "actual_usd", "plan_usd"])


def gen_capital_plan() -> pd.DataFrame:
    rng = rng_for("capital_plan")
    rows = []
    for i, q in enumerate(quarter_ends(8)):
        target = 4.2e9
        re = target * (0.9 + i * 0.02) * rng.uniform(0.98, 1.03)
        rows.append((q, round(re, 2), round(target, 2), round(rng.uniform(5.5e9, 6.5e9), 2)))
    return pd.DataFrame(rows, columns=["quarter_end_date", "retained_earnings_usd", "retained_earnings_target_usd", "activity_based_stock_usd"])


# ---------------------------------------------------------------------------
# 19-23. MISSION / AHP TABLES
# ---------------------------------------------------------------------------
def gen_ahp_applications() -> pd.DataFrame:
    rng = rng_for("ahp_applications")
    n = 420
    units = rng.integers(4, 220, n)
    subsidy_per_unit = np.round(rng.uniform(15_000, 150_000, n), 2)
    subsidy = np.round(np.minimum(units * subsidy_per_unit, 3_000_000), 2)
    return pd.DataFrame({
        "application_id": [f"AHP-{i:04d}" for i in range(1, n + 1)],
        "member_id": rng.choice(member_id_list(), size=n),
        "project_name": [f"{rng.choice(_LAST_NAMES)} {rng.choice(['Commons','Village','Terrace','Landing','Homes','Place','Crossing'])}" for _ in range(n)],
        "program": rng.choice(["Competitive AHP", "AHP General Fund"], size=n, p=[0.7, 0.3]),
        "project_type": rng.choice(["Rental", "Homeownership"], size=n, p=[0.68, 0.32]),
        "status": rng.choice(["Received", "Scored", "Awarded", "Disbursed", "At Risk of Close", "De-obligated"], size=n, p=[0.12, 0.15, 0.28, 0.30, 0.09, 0.06]),
        "round_year": rng.choice([2024, 2025, 2026], size=n, p=[0.3, 0.4, 0.3]),
        "state": rng.choice(STATES, size=n, p=STATE_W),
        "units_total": units,
        "units_targeted": (units * rng.uniform(0.5, 1.0, n)).astype(int),
        "subsidy_requested_usd": subsidy,
        "subsidy_per_unit_usd": subsidy_per_unit,
        "tclp_high_need_flag": rng.random(n) < 0.4,
        "need_for_subsidy_ratio": np.round(rng.uniform(0.6, 1.4, n), 3),
        "score": np.round(rng.uniform(62, 79, n), 4),
    })


def gen_homeownership_setaside() -> pd.DataFrame:
    rng = rng_for("homeownership_setaside")
    n = 1200
    sa = pd.DataFrame({
        "allocation_id": [f"SA-{i:05d}" for i in range(1, n + 1)],
        "member_id": rng.choice(member_id_list(), size=n),
        "product": rng.choice(["Home$tart (Down Payment Assistance)", "Native American Homeownership Initiative"], size=n, p=[0.82, 0.18]),
        "program_year": rng.choice([2025, 2026], size=n, p=[0.45, 0.55]),
        "allocated_usd": np.round(rng.uniform(5_000, 30_000, n), 2),
    })
    sa["used_usd"] = np.round(sa["allocated_usd"] * rng.uniform(0, 1, n), 2)
    sa["expiration_date"] = [dt.date(int(y), 12, 31) for y in sa["program_year"]]
    return sa


def gen_cip_cica_activity() -> pd.DataFrame:
    rng = rng_for("cip_cica_activity")
    n = 2000
    return pd.DataFrame({
        "activity_id": [f"CICA-{i:05d}" for i in range(1, n + 1)],
        "member_id": rng.choice(member_id_list(), size=n),
        "activity_date": [HISTORY_START + dt.timedelta(days=int(rng.integers(0, 540))) for _ in range(n)],
        "program": rng.choice(["CIP", "CICA"], size=n, p=[0.55, 0.45]),
        "purpose": rng.choice(["Housing", "Economic Development"], size=n, p=[0.6, 0.4]),
        "amount_usd": np.round(np.exp(rng.normal(14.6, 0.9, n)), 2),
        "units": rng.integers(0, 120, n),
        "state": rng.choice(STATES, size=n, p=STATE_W),
    })


def gen_mission_units() -> pd.DataFrame:
    rng = rng_for("mission_units")
    ahp = gen_ahp_applications()
    rows, muid = [], 1
    for _, a in ahp.iterrows():
        if a.status in ("Awarded", "Disbursed"):
            n = int(a.units_targeted)
            vli = int(n * rng.uniform(0.2, 0.6))
            rows.append((f"MU-{muid:05d}", "AHP", a.state, "Very Low Income", bool(rng.random() < 0.35), vli))
            muid += 1
            rows.append((f"MU-{muid:05d}", "AHP", a.state, "Low or Moderate Income", bool(rng.random() < 0.35), n - vli))
            muid += 1
    return pd.DataFrame(rows, columns=["mission_unit_id", "source_program", "state", "income_tier", "rural_flag", "units"])


def gen_pledge_activity() -> pd.DataFrame:
    rng = rng_for("pledge_activity")
    programs = ["Competitive AHP", "Home$tart", "Native American Homeownership", "CIP/CICA", "Voluntary Contributions"]
    rows, plid = [], 1
    for prog in programs:
        for mth in month_ends(dt.date(TODAY.year, 1, 31), TODAY):
            for st in rng.choice(STATES, size=6, replace=False, p=STATE_W):
                committed = rng.uniform(50_000, 900_000)
                rows.append((f"PLG-{plid:05d}", mth, prog, st, round(committed, 2), round(committed * rng.uniform(0.3, 0.95), 2)))
                plid += 1
    return pd.DataFrame(rows, columns=["pledge_id", "activity_month", "program", "state", "committed_usd", "disbursed_usd"])


# ---------------------------------------------------------------------------
# 24. EADVANTAGE ACTIVITY
# ---------------------------------------------------------------------------
SCREENS = [("Advance Dashboard", "advance_daily_balances feed"), ("Collateral Summary", "pledged_collateral feed"),
           ("Rate Indications", "advance_pricing_daily feed"), ("Statements & Reports", "general_ledger feed"),
           ("MPF Delivery", "mpf_loans feed"), ("AHP & Grants", "ahp_applications feed")]


def gen_eadvantage_activity() -> pd.DataFrame:
    rng = rng_for("eadvantage_activity")
    member_ids = member_id_list()
    n = 80000
    sess_members = rng.choice(member_ids, size=n)
    non_transactors = set(rng.choice(member_ids, size=int(N_MEMBERS * 0.12), replace=False))
    rows = []
    for i in range(n):
        mid = sess_members[i]
        d = TODAY - dt.timedelta(days=int(rng.integers(0, 180)))
        screen, feed = SCREENS[rng.integers(0, len(SCREENS))]
        if mid in non_transactors:
            action = "Login" if rng.random() < 0.7 else "View"
        else:
            action = rng.choice(["Login", "View", "Transaction"], p=[0.4, 0.35, 0.25])
        rows.append((f"SESS-{i+1:06d}", mid, d, screen, feed, action, bool(action == "Transaction")))
    return pd.DataFrame(rows, columns=["session_id", "member_id", "session_date", "screen", "feed_name", "action_type", "transacted_flag"])


# ---------------------------------------------------------------------------
# 25-34. OPS / GOVERNANCE TABLES
# ---------------------------------------------------------------------------
FHFA_REPORTS = ["FHFA Call Report System Submission", "Advances & Collateral Quarterly (ACES)",
                "Member Financial Data Report", "AHP/CIP Mission Activities Report",
                "Capital Stock & Dividend Report", "Consolidated Obligations Report"]


def gen_ops_data_quality_exceptions() -> pd.DataFrame:
    rng = rng_for("ops_data_quality_exceptions")
    cur_q = (TODAY.month - 1) // 3
    q_start = dt.date(TODAY.year, cur_q * 3 + 1, 1)
    q_end = (dt.date(TODAY.year, cur_q * 3 + 4, 1) - dt.timedelta(days=1)) if cur_q < 3 else dt.date(TODAY.year, 12, 31)
    q_span = (q_end - q_start).days
    q_label = f"Q{cur_q + 1} {TODAY.year}"
    rows = []
    for i in range(1, 61):
        rows.append((f"DQ-{i:04d}", rng.choice(FHFA_REPORTS), "FHFA",
                     q_start + dt.timedelta(days=int(rng.integers(0, q_span + 1))), q_label,
                     f"SRC-{rng.integers(1, 17):03d}", rng.choice(["Open", "Resolved"], p=[0.45, 0.55]),
                     rng.choice(["High", "Medium", "Low"], p=[0.25, 0.5, 0.25]),
                     rng.choice(["Missing values", "Failed reconciliation", "Schema drift", "Late arrival", "Duplicate records"])))
    return pd.DataFrame(rows, columns=["exception_id", "report_name", "regulator", "report_due_date", "quarter",
                                       "source_system_id", "status", "severity", "description"])


def gen_ops_column_lineage() -> pd.DataFrame:
    rows = [
        ("member_credit_rating", "SRC-019", "FFIEC Call Report ingest", "bronze.ffiec_call_raw", "Bronze", "FHFA Call Report System Submission"),
        ("member_credit_rating", "SRC-019", "bronze.ffiec_call_raw", "silver.member_financials", "Silver", "FHFA Call Report System Submission"),
        ("member_credit_rating", "SRC-002", "silver.member_financials", "gold.member_credit_ratings", "Gold", "FHFA Call Report System Submission"),
        ("member_credit_rating", "SRC-002", "gold.member_credit_ratings", "reg.fhfa_crs_submission", "Reporting", "FHFA Call Report System Submission"),
    ]
    return pd.DataFrame([(f"LIN-{i+1:03d}", *r) for i, r in enumerate(rows)],
                        columns=["lineage_id", "field_name", "source_system_id", "upstream_object", "downstream_object", "layer", "submission_name"])


def gen_ops_bi_refresh() -> pd.DataFrame:
    rng = rng_for("ops_bi_refresh")
    dash = [("Advances Executive View", "Qlik"), ("Collateral Risk Monitor", "Power BI"), ("Member 360", "Qlik"),
            ("Treasury Daily", "Power BI"), ("Mission & AHP", "Qlik"), ("Delinquency Trends", "Power BI")]
    rows, biid = [], 1
    for name, tool in dash:
        for d in [TODAY - dt.timedelta(days=x) for x in range(0, 30)]:
            sla = 60
            actual = sla + (rng.integers(5, 90) if rng.random() < 0.18 else -rng.integers(0, 40))
            rows.append((f"BIR-{biid:05d}", name, tool, d, sla, int(actual), bool(actual <= sla),
                         f"extract_{name.lower().replace(' ', '_')}"))
            biid += 1
    return pd.DataFrame(rows, columns=["refresh_id", "dashboard_name", "bi_tool", "refresh_date", "sla_minutes",
                                       "actual_minutes", "sla_met_flag", "extract_job"])


def gen_ops_metric_reconciliation() -> pd.DataFrame:
    rng = rng_for("ops_metric_reconciliation")
    metrics = ["Total Advances Outstanding", "Total Pledged Collateral", "Member Advance Balance",
               "Consolidated Obligations", "AHP Assessment Accrual"]
    rows = []
    for i, m in enumerate(metrics):
        auth_val = rng.uniform(1e8, 1.2e11)
        qlik = auth_val * rng.uniform(0.999, 1.001)
        pbi = auth_val * rng.uniform(0.985, 1.015)
        rows.append((f"REC-{i+1:03d}", m, round(qlik, 2), round(pbi, 2),
                     rng.choice(["gold.advances", "gold.collateral", "gold.bank_position"]), round(auth_val, 2),
                     TODAY, bool(abs(qlik - pbi) / auth_val > 0.005)))
    return pd.DataFrame(rows, columns=["reconciliation_id", "metric_name", "qlik_value", "powerbi_value",
                                       "authoritative_table", "authoritative_value", "as_of_date", "mismatch_flag"])


def gen_ops_access_events() -> pd.DataFrame:
    rng = rng_for("ops_access_events")
    member_ids = member_id_list()
    roles = ["Credit Analyst", "Member Services", "Finance", "Executive", "External Auditor", "Data Engineer"]
    rows = []
    for i in range(1, 1201):
        role = rng.choice(roles)
        cls = rng.choice(["Nonpublic Member Financial", "Public", "Internal"], p=[0.5, 0.2, 0.3])
        in_policy = not (cls == "Nonpublic Member Financial" and role in ("Member Services", "Data Engineer") and rng.random() < 0.5)
        user = f"{rng.choice(_LAST_NAMES).lower()}.{rng.choice(list('abcdefghijklmnop'))}{int(rng.integers(1, 99))}"
        rows.append((f"ACC-{i:05d}", user, TODAY - dt.timedelta(days=int(rng.integers(0, 90))),
                     rng.choice(["member_credit_ratings", "call_reports_quarterly", "pledged_collateral", "advance_daily_balances"]),
                     rng.choice(member_ids), cls, role, bool(in_policy)))
    return pd.DataFrame(rows, columns=["event_id", "user_name", "access_time", "data_object", "member_id",
                                       "data_classification", "user_role", "in_policy_flag"])


def gen_ops_model_inventory() -> pd.DataFrame:
    rng = rng_for("ops_model_inventory")
    models = [("MDL-CREDIT-01", "Member Credit Rating Model", "Credit"), ("MDL-CREDIT-02", "Insurance Member Credit Model", "Credit"),
              ("MDL-COLL-01", "Collateral Valuation Model", "Collateral"), ("MDL-COLL-02", "Haircut Calibration Model", "Collateral"),
              ("MDL-PREPAY-01", "Prepayment Model", "Market"), ("MDL-AHP-01", "AHP Scoring Assist Model", "Mission"),
              ("MDL-AML-01", "Member Transaction Monitoring", "Compliance")]
    rows = []
    for mid_, name, typ in models:
        last_val = TODAY - dt.timedelta(days=int(rng.integers(120, 700)))
        due = last_val + dt.timedelta(days=365)
        owner = f"{rng.choice(_LAST_NAMES)}, {rng.choice(['A.','B.','C.','D.','E.'])}"
        rows.append((mid_, name, typ, owner, last_val, due, True, "Overdue" if due < TODAY else "Current"))
    return pd.DataFrame(rows, columns=["model_id", "model_name", "model_type", "owner", "last_validation_date",
                                       "validation_due_date", "touches_member_data_flag", "validation_status"])


def gen_ops_examiner_requests() -> pd.DataFrame:
    rng = rng_for("ops_examiner_requests")
    req_types = ["Member Credit File", "Collateral Position", "Advance Detail", "AHP Project File",
                 "Model Documentation", "Data Lineage", "Access Report"]
    rows, erid = [], 1
    for cycle, mult in [("2025 Exam Cycle", 1.25), ("2026 Exam Cycle", 1.0)]:
        for rt in req_types:
            for _ in range(int(rng.integers(4, 12))):
                recv = TODAY - dt.timedelta(days=int(rng.integers(30, 400)))
                base = {"Member Credit File": 3, "Collateral Position": 4, "Advance Detail": 2, "AHP Project File": 5,
                        "Model Documentation": 9, "Data Lineage": 11, "Access Report": 6}[rt]
                ta = max(1, int(rng.normal(base * mult, 2)))
                rows.append((f"REQ-{erid:04d}", cycle, rt, recv, recv + dt.timedelta(days=ta), ta))
                erid += 1
    return pd.DataFrame(rows, columns=["request_id", "exam_cycle", "request_type", "received_date", "fulfilled_date", "turnaround_days"])


def gen_ops_pipeline_cost() -> pd.DataFrame:
    rng = rng_for("ops_pipeline_cost")
    pipelines = [("Advances ETL", True), ("Collateral ETL", True), ("Member Financials ETL", True),
                 ("MPF Servicing Load", False), ("Regulatory Reporting", True), ("AHP Pipeline", False), ("Investments Load", True)]
    rows, pcid = [], 1
    for name, dual in pipelines:
        for mth in month_ends(dt.date(TODAY.year, 1, 31), TODAY):
            for platform in (["SQL Server", "Microsoft Fabric"] if dual else ["SQL Server"]):
                cost = rng.uniform(8_000, 45_000) * (1.1 if platform == "Microsoft Fabric" else 1.0)
                rows.append((f"PLC-{pcid:05d}", name, platform, mth, round(cost, 2), bool(dual)))
                pcid += 1
    return pd.DataFrame(rows, columns=["cost_id", "pipeline_name", "platform", "cost_month", "monthly_cost_usd", "is_dual_run_flag"])


def gen_ops_gl_reconciliation() -> pd.DataFrame:
    rng = rng_for("ops_gl_reconciliation")
    rows = []
    for i, (screen, feed) in enumerate(SCREENS):
        gl_bal = rng.uniform(1e7, 5e10)
        feed_bal = gl_bal * rng.uniform(0.995, 1.005)
        rows.append((f"GLR-{i+1:03d}", feed, screen, TODAY - dt.timedelta(days=int(rng.integers(0, 45))),
                     round(gl_bal, 2), round(feed_bal, 2), round(feed_bal - gl_bal, 2)))
    return pd.DataFrame(rows, columns=["recon_id", "feed_name", "screen", "last_reconciled_date", "gl_balance_usd",
                                       "feed_balance_usd", "variance_usd"])


def gen_ops_ai_content_sources() -> pd.DataFrame:
    sources = [
        ("AHP Implementation Plan 2026", "Policy Document", "AHP Program Manager", True),
        ("Targeted Community Lending Plan", "Policy Document", "Community Investment Officer", True),
        ("AHP Scoring Criteria FAQ", "Knowledge Base", "AHP Program Manager", True),
        ("Member Outreach Emails", "Unstructured Email Archive", "Unapproved", False),
        ("Public FHFA Regulations", "External Web", "Compliance", True),
        ("Historical Award Data", "Structured Table", "Data Governance", True),
    ]
    return pd.DataFrame([(f"AIS-{i+1:03d}", "Affordable Housing Virtual Assistant", src, typ, appr, bool(gov))
                         for i, (src, typ, appr, gov) in enumerate(sources)],
                        columns=["source_id", "assistant_name", "content_source", "source_type", "approver", "governed_flag"])


# ---------------------------------------------------------------------------
# Table/column comments + date columns (drives finalize()) — verbatim from the
# original generator so Genie keeps its rich metadata.
# ---------------------------------------------------------------------------
COMMENTS: dict[str, dict] = {
    "members": {"table": "Synthetic FHLB Des Moines member institutions (fictional). One row per member.",
                "dates": ["membership_date"], "cols": {
        "member_id": "Unique member identifier (MEM-XXXXX).", "member_name": "Fictional member institution name.",
        "member_type": "Charter type: Commercial Bank, Credit Union, Thrift, Insurance Company, CDFI.",
        "charter_state": "Two-letter state or Pacific territory code in the FHLB Des Moines district.",
        "city": "Headquarters city.", "is_cdfi": "True if the member is a Community Development Financial Institution.",
        "asset_size_usd": "Total assets in USD (synthetic).",
        "collateral_status": "Collateral pledge status: Blanket Lien, Specific Listing, or Delivery.",
        "membership_date": "Date the institution joined the Bank.", "is_borrowing": "True if the member currently uses advances.",
        "is_active": "True if the membership is active."}},
    "eligible_nonmembers": {"table": "Synthetic in-district institutions eligible for membership but not yet members (prospect list).",
                            "dates": [], "cols": {
        "prospect_id": "Unique prospect identifier.", "institution_name": "Fictional institution name.",
        "member_type": "Charter type.", "state": "State or territory code.", "asset_size_usd": "Total assets in USD.",
        "mortgage_origination_volume_usd": "Annual mortgage origination volume in USD.",
        "similarity_score": "0-100 lookalike score vs the Bank's best-performing members (higher = better prospect)."}},
    "ops_source_systems": {"table": "Synthetic inventory of source systems feeding the data estate: 16 legacy SQL Server instances, a Microsoft Fabric build, and external feeds.",
                           "dates": [], "cols": {
        "source_system_id": "Unique source system identifier.", "system_name": "System / instance name.",
        "system_type": "SQL Server, Microsoft Fabric, External Feed, or Application.",
        "instance_label": "Human-readable instance label.", "environment": "Production or Migration."}},
    "advance_daily_balances": {"table": "Synthetic daily advance positions by member (sampled every ~3 days over 18 months). Raw balances; aggregate in queries.",
                               "dates": ["business_date", "origination_date", "maturity_date", "repricing_date"], "cols": {
        "advance_id": "Unique advance position row id.", "member_id": "FK to members.member_id.", "business_date": "Position date.",
        "product": "Advance product: Fixed Rate, SOFR-Indexed, CIP, CICA.", "index_type": "Rate index: SOFR or Fixed.",
        "outstanding_par_usd": "Outstanding par balance in USD.", "accrued_interest_usd": "Accrued interest in USD for the period.",
        "rate_pct": "Advance coupon rate in percent.", "origination_date": "Advance origination date.",
        "maturity_date": "Advance maturity date.", "repricing_date": "Next repricing date (equals maturity for fixed-rate)."}},
    "pledged_collateral": {"table": "Synthetic pledged collateral lots by member with lendable value and haircut. Unused capacity = lendable_value_usd minus advances outstanding.",
                           "dates": ["as_of_date"], "cols": {
        "lot_id": "Unique collateral lot id.", "member_id": "FK to members.member_id.", "as_of_date": "Collateral valuation date.",
        "collateral_type": "Collateral category (e.g., 1-4 Family Mortgage, Agency MBS).",
        "unpaid_principal_usd": "Unpaid principal balance / market value of the pledged lot in USD.",
        "lendable_value_usd": "Lendable (post-haircut) collateral value in USD.", "haircut_pct": "Applied collateral haircut in percent."}},
    "collateral_reviews": {"table": "Synthetic collateral verification review results by collateral type and month. Rising exception rates suggest haircut changes.",
                           "dates": ["review_date"], "cols": {
        "review_id": "Unique review id.", "review_date": "Month-end review date.", "collateral_type": "Collateral category reviewed.",
        "items_reviewed": "Number of collateral items sampled.", "exceptions_found": "Number of exceptions identified.",
        "exception_rate_pct": "Exception rate in percent."}},
    "letters_of_credit": {"table": "Synthetic standby letters of credit issued to members by purpose.",
                          "dates": ["issue_date", "expiration_date"], "cols": {
        "loc_id": "Unique letter-of-credit id.", "member_id": "FK to members.member_id.",
        "purpose": "LOC purpose (Public Unit Deposit, Housing/Community Development, ALM, Other).",
        "notional_usd": "Notional amount in USD.", "issue_date": "Issue date.", "expiration_date": "Expiration date.",
        "status": "Active or Expired."}},
    "member_credit_ratings": {"table": "Synthetic internal member credit rating history. next_review_due before today means past the AB 2024-03 refresh cadence.",
                              "dates": ["as_of_date", "next_review_due"], "cols": {
        "rating_id": "Unique rating record id.", "member_id": "FK to members.member_id.", "as_of_date": "Effective date of the rating.",
        "internal_rating": "Internal credit rating grade (1 Strong to 5 Doubtful).", "prior_rating": "Prior rating grade.",
        "next_review_due": "Date the next rating refresh is due (AB 2024-03 cadence).", "cadence_days": "Required refresh cadence in days.",
        "rating_model_id": "FK to ops_model_inventory.model_id for the rating model used."}},
    "call_reports_quarterly": {"table": "Synthetic quarterly FFIEC call-report metrics per member. Some members show planted quarter-over-quarter deterioration.",
                               "dates": ["quarter_end_date"], "cols": {
        "report_id": "Unique call report row id.", "member_id": "FK to members.member_id.", "quarter_end_date": "Quarter-end date.",
        "total_assets_usd": "Total assets in USD.", "uninsured_deposit_ratio_pct": "Uninsured deposits as percent of total deposits.",
        "brokered_deposit_growth_pct": "Quarter-over-quarter brokered deposit growth percent.",
        "unrealized_securities_loss_usd": "Unrealized securities gain/loss in USD (negative = loss / AOCI).",
        "fed_facility_usage_flag": "True if the member shows discount window / Federal Reserve facility usage signals.",
        "tier1_leverage_ratio_pct": "Tier 1 leverage ratio percent."}},
    "mortgage_originations": {"table": "Synthetic monthly mortgage origination activity by member, with secondary-market outlet. Members originating but with sold_to != 'MPF' are candidates not delivering into the MPF Program.",
                              "dates": ["origination_month"], "cols": {
        "origination_id": "Unique origination record id.", "member_id": "FK to members.member_id.",
        "origination_month": "Month-end of origination activity.", "loan_count": "Number of loans originated.",
        "origination_volume_usd": "Origination dollar volume in USD.",
        "sold_to": "Secondary-market outlet: MPF, Fannie Mae, Freddie Mac, Ginnie Mae, or Held in Portfolio."}},
    "mpf_loans": {"table": "Synthetic Mortgage Partnership Finance (MPF) / Acquired Member Asset loan book held by the Bank. Used for housing-goals low-income and low-income-area shares.",
                  "dates": [], "cols": {
        "loan_id": "Unique MPF loan id.", "member_id": "FK to members.member_id (the Participating Financial Institution / PFI).",
        "vintage_year": "Origination vintage year.", "current_upb_usd": "Current unpaid principal balance in USD.",
        "occupancy": "Occupancy type.", "note_rate_pct": "Note rate percent.",
        "low_income_flag": "True if borrower income qualifies as low-income (FHFA housing goals).",
        "low_income_area_flag": "True if property is in a low-income area (FHFA housing goals).", "product": "MPF product variant."}},
    "mpf_servicing_monthly": {"table": "Synthetic monthly MPF servicing/delinquency data from the MPF Provider (FHLBank Chicago), by loan, PFI, and vintage.",
                              "dates": ["activity_month"], "cols": {
        "servicing_id": "Unique servicing record id.", "loan_id": "FK to mpf_loans.loan_id.", "member_id": "FK to members.member_id (PFI).",
        "activity_month": "Servicing report month-end.", "vintage_year": "Loan vintage year.",
        "delinquency_bucket": "Delinquency status: Current, 30-59, 60-89, 90+ Days, In Foreclosure.",
        "high_level_concern_flag": "True if the loan is flagged High Level Concern.", "upb_usd": "Reported unpaid principal balance in USD."}},
    "investment_holdings": {"table": "Synthetic investment portfolio positions (agency MBS and related). Unrealized gain/loss by vintage and duration bucket.",
                            "dates": [], "cols": {
        "holding_id": "Unique holding id.", "security_type": "Security type (Agency MBS, Agency CMO, US Treasury, Agency Debenture).",
        "cusip": "Synthetic CUSIP.", "vintage_year": "Vintage year.", "duration_bucket": "Duration bucket (0-2y, 2-5y, 5-10y, 10y+).",
        "book_value_usd": "Amortized book value in USD.", "market_value_usd": "Fair market value in USD.",
        "unrealized_gain_loss_usd": "Unrealized gain (positive) or loss (negative) in USD."}},
    "prepayment_speeds": {"table": "Synthetic actual vs forecast prepayment speeds (CPR) by portfolio and month.",
                          "dates": ["activity_month"], "cols": {
        "prepay_id": "Unique row id.", "portfolio": "Portfolio: MPF Loans or Agency MBS.", "activity_month": "Month-end.",
        "actual_cpr_pct": "Actual conditional prepayment rate percent.", "forecast_cpr_pct": "Forecast/assumed CPR percent in the income forecast."}},
    "co_issuances": {"table": "Synthetic consolidated obligation (CO) issuances with spread to Treasuries.",
                     "dates": ["issue_date"], "cols": {
        "issuance_id": "Unique issuance id.", "issue_date": "Issuance date.", "co_type": "Consolidated obligation type.",
        "tenor_months": "Tenor in months.", "par_usd": "Par amount issued in USD.",
        "spread_to_treasury_bps": "Issuance spread to Treasuries in basis points.", "coupon_pct": "Coupon rate percent."}},
    "market_rates_daily": {"table": "Synthetic daily market rates: SOFR and Treasury curve points. Use for SOFR sensitivity and CO spread analysis.",
                           "dates": ["business_date"], "cols": {
        "business_date": "Rate date.", "sofr_pct": "Secured Overnight Financing Rate percent.",
        "ust_3m_pct": "US Treasury 3-month yield percent.", "ust_2y_pct": "US Treasury 2-year yield percent.",
        "ust_5y_pct": "US Treasury 5-year yield percent.", "ust_10y_pct": "US Treasury 10-year yield percent."}},
    "advance_pricing_daily": {"table": "Synthetic weekly advance pricing vs member funding alternatives (brokered deposits) by maturity point.",
                              "dates": ["business_date"], "cols": {
        "price_id": "Unique row id.", "business_date": "Pricing date.", "tenor_months": "Maturity point in months.",
        "advance_rate_pct": "Indicative advance rate percent.",
        "brokered_deposit_rate_pct": "Comparable brokered deposit rate percent members could obtain instead."}},
    "bank_position_daily": {"table": "Synthetic bank-level daily balance sheet snapshot. Core mission asset ratio = (total_advances_usd + total_ama_usd) / consolidated_obligations_usd.",
                            "dates": ["business_date"], "cols": {
        "business_date": "Position date.", "total_advances_usd": "Total advances outstanding in USD (bank-level).",
        "total_ama_usd": "Total Acquired Member Assets (MPF) in USD.",
        "consolidated_obligations_usd": "Consolidated obligations outstanding in USD.", "net_income_mtd_usd": "Month-to-date net income in USD."}},
    "advance_forecast_quarterly": {"table": "Synthetic quarterly advance forecast by member segment. Compare to actual advance balances to compute variance.",
                                   "dates": ["quarter_end_date"], "cols": {
        "quarter_end_date": "Quarter-end date.", "member_segment": "Member segment (by member_type).",
        "forecast_advances_usd": "Forecast advance balance in USD."}},
    "financials_actual_vs_forecast": {"table": "Synthetic actual vs forecast financial line items by quarter (last 4 quarters). Spread is in percent; dollar lines in USD.",
                                      "dates": ["quarter_end_date"], "cols": {
        "fin_id": "Unique row id.", "quarter_end_date": "Quarter-end date.", "line_item": "Financial line item name.",
        "actual_value": "Actual value (USD, or percent for Net Interest Spread).", "forecast_value": "Forecast value.",
        "variance_value": "Actual minus forecast."}},
    "vendor_spend": {"table": "Synthetic vendor / contractual services spend by category and month vs plan (year to date).",
                     "dates": ["spend_month"], "cols": {
        "spend_id": "Unique row id.", "spend_month": "Spend month-end.", "vendor_category": "Vendor category (e.g., Consulting, Cloud Infrastructure).",
        "actual_usd": "Actual spend in USD.", "plan_usd": "Planned spend in USD."}},
    "capital_plan": {"table": "Synthetic quarterly capital plan: retained earnings vs target and activity-based capital stock.",
                     "dates": ["quarter_end_date"], "cols": {
        "quarter_end_date": "Quarter-end date.", "retained_earnings_usd": "Retained earnings in USD.",
        "retained_earnings_target_usd": "Capital plan retained earnings target in USD.",
        "activity_based_stock_usd": "Activity-based capital stock in USD."}},
    "ahp_applications": {"table": "Synthetic Affordable Housing Program (AHP) applications through the funding pipeline. need_for_subsidy_ratio < 1 suggests overfunding; status tracks received->scored->awarded->disbursed with at-risk/de-obligated.",
                         "dates": [], "cols": {
        "application_id": "Unique application id.", "member_id": "FK to members.member_id (sponsoring member).",
        "project_name": "Fictional project name.", "program": "Competitive AHP or AHP General Fund.", "project_type": "Rental or Homeownership.",
        "status": "Pipeline status: Received, Scored, Awarded, Disbursed, At Risk of Close, De-obligated.", "round_year": "Funding round year.",
        "state": "Project state/territory.", "units_total": "Total housing units in the project.", "units_targeted": "AHP-targeted (income-qualified) units.",
        "subsidy_requested_usd": "AHP subsidy requested in USD (capped at project max).",
        "subsidy_per_unit_usd": "Subsidy per targeted unit in USD (lower is more efficient).",
        "tclp_high_need_flag": "True if in a Targeted Community Lending Plan high-need geography.",
        "need_for_subsidy_ratio": "Need-for-subsidy analysis ratio for rentals (<1 = potentially overfunded).", "score": "AHP scoring result."}},
    "homeownership_setaside": {"table": "Synthetic homeownership set-aside / down payment assistance allocations by member. Unused = allocated_usd - used_usd; watch expiration_date.",
                               "dates": ["expiration_date"], "cols": {
        "allocation_id": "Unique allocation id.", "member_id": "FK to members.member_id.",
        "product": "Set-aside product (Home$tart or Native American Homeownership Initiative).", "program_year": "Program year.",
        "allocated_usd": "Allocated subsidy in USD.", "used_usd": "Used subsidy in USD.", "expiration_date": "Allocation expiration date."}},
    "cip_cica_activity": {"table": "Synthetic Community Investment Program (CIP) and Community Investment Cash Advance (CICA) activity, split by housing vs economic development.",
                          "dates": ["activity_date"], "cols": {
        "activity_id": "Unique activity id.", "member_id": "FK to members.member_id.", "activity_date": "Activity date.",
        "program": "CIP or CICA.", "purpose": "Housing or Economic Development.", "amount_usd": "Advance / investment amount in USD.",
        "units": "Housing units supported (if applicable).", "state": "State/territory."}},
    "mission_units": {"table": "Synthetic housing units supported this year by income tier and rural flag, in the format the FHFA mission-activities report uses.",
                      "dates": [], "cols": {
        "mission_unit_id": "Unique row id.", "source_program": "Source program (AHP, set-aside).", "state": "State/territory.",
        "income_tier": "Income tier: Very Low Income or Low or Moderate Income.", "rural_flag": "True if rural.", "units": "Number of units."}},
    "pledge_activity": {"table": "Synthetic progress toward the $200M housing affordability pledge, by program, state, and month.",
                        "dates": ["activity_month"], "cols": {
        "pledge_id": "Unique row id.", "activity_month": "Activity month-end.", "program": "Pledge program bucket.",
        "state": "State/territory.", "committed_usd": "Committed dollars in USD.", "disbursed_usd": "Disbursed dollars in USD."}},
    "eadvantage_activity": {"table": "Synthetic eAdvantage member-portal session activity. Identify members that log in but have not transacted in 90 days; feed_name shows what data feeds each screen.",
                            "dates": ["session_date"], "cols": {
        "session_id": "Unique session id.", "member_id": "FK to members.member_id.", "session_date": "Session date.",
        "screen": "eAdvantage screen viewed.", "feed_name": "Upstream data feed powering the screen.",
        "action_type": "Login, View, or Transaction.", "transacted_flag": "True if the session included a transaction."}},
    "ops_data_quality_exceptions": {"table": "Synthetic data-quality exceptions on regulatory reports, traced to a source system. Open exceptions on reports due this quarter are the CIO exam risk.",
                                    "dates": ["report_due_date"], "cols": {
        "exception_id": "Unique exception id.", "report_name": "Regulatory report name.", "regulator": "Regulator (FHFA).",
        "report_due_date": "Report due date.", "quarter": "Reporting quarter label.",
        "source_system_id": "FK to ops_source_systems.source_system_id.", "status": "Open or Resolved.",
        "severity": "High, Medium, or Low.", "description": "Exception description."}},
    "ops_column_lineage": {"table": "Synthetic column-level lineage for the member credit rating field, from source ingestion to the FHFA-reported value.",
                           "dates": [], "cols": {
        "lineage_id": "Unique edge id.", "field_name": "Tracked field name.",
        "source_system_id": "FK to ops_source_systems.source_system_id.", "upstream_object": "Upstream table/object.",
        "downstream_object": "Downstream table/object.", "layer": "Medallion / reporting layer.",
        "submission_name": "Regulatory submission the field flows into."}},
    "ops_bi_refresh": {"table": "Synthetic BI dashboard refresh log for Qlik and Power BI over the last 30 days, with SLA status and the extract job responsible.",
                       "dates": ["refresh_date"], "cols": {
        "refresh_id": "Unique refresh id.", "dashboard_name": "Dashboard name.", "bi_tool": "Qlik or Power BI.",
        "refresh_date": "Refresh date.", "sla_minutes": "Refresh SLA in minutes.", "actual_minutes": "Actual refresh duration in minutes.",
        "sla_met_flag": "True if refresh met SLA.", "extract_job": "Extract job that produced the data."}},
    "ops_metric_reconciliation": {"table": "Synthetic reconciliation of the same metric across Qlik and Power BI vs the authoritative Lakehouse table.",
                                  "dates": ["as_of_date"], "cols": {
        "reconciliation_id": "Unique row id.", "metric_name": "Business metric name.", "qlik_value": "Value shown in Qlik.",
        "powerbi_value": "Value shown in Power BI.", "authoritative_table": "Authoritative source table.",
        "authoritative_value": "Authoritative value.", "as_of_date": "As-of date.",
        "mismatch_flag": "True if Qlik and Power BI disagree beyond tolerance."}},
    "ops_access_events": {"table": "Synthetic access log over the last 90 days for nonpublic member financial data. in_policy_flag = False means access outside the role-based policy.",
                          "dates": ["access_time"], "cols": {
        "event_id": "Unique event id.", "user_name": "User who accessed the data.", "access_time": "Access date.",
        "data_object": "Data object accessed.", "member_id": "FK to members.member_id whose data was accessed.",
        "data_classification": "Data sensitivity classification.", "user_role": "Accessing user's role.",
        "in_policy_flag": "True if the access complied with role-based policy."}},
    "ops_model_inventory": {"table": "Synthetic model inventory with last/next validation dates under FHFA model risk guidance. validation_due_date before today = past due.",
                            "dates": ["last_validation_date", "validation_due_date"], "cols": {
        "model_id": "Unique model id.", "model_name": "Model name.", "model_type": "Credit, Collateral, Market, Mission, or Compliance.",
        "owner": "Model owner.", "last_validation_date": "Date of last validation.", "validation_due_date": "Next validation due date.",
        "touches_member_data_flag": "True if the model touches member data.", "validation_status": "Current or Overdue."}},
    "ops_examiner_requests": {"table": "Synthetic examiner data-request log across exam cycles, with turnaround days by request type. Compare cycles to show evidence-velocity improvement.",
                              "dates": ["received_date", "fulfilled_date"], "cols": {
        "request_id": "Unique request id.", "exam_cycle": "Exam cycle label.", "request_type": "Type of examiner request.",
        "received_date": "Date the request was received.", "fulfilled_date": "Date the request was fulfilled.",
        "turnaround_days": "Turnaround time in days."}},
    "ops_pipeline_cost": {"table": "Synthetic monthly pipeline run cost by platform. Pipelines with is_dual_run_flag run on both legacy SQL Server and Microsoft Fabric; sum both platforms for dual-run cost.",
                          "dates": ["cost_month"], "cols": {
        "cost_id": "Unique row id.", "pipeline_name": "Pipeline name.", "platform": "SQL Server or Microsoft Fabric.",
        "cost_month": "Cost month-end.", "monthly_cost_usd": "Monthly run cost in USD.", "is_dual_run_flag": "True if the pipeline runs in parallel on both estates."}},
    "ops_gl_reconciliation": {"table": "Synthetic reconciliation of eAdvantage member-facing feeds against the general ledger, with last reconciled date.",
                              "dates": ["last_reconciled_date"], "cols": {
        "recon_id": "Unique row id.", "feed_name": "Data feed powering an eAdvantage screen.", "screen": "eAdvantage screen.",
        "last_reconciled_date": "Date the feed was last reconciled to the GL.", "gl_balance_usd": "General ledger balance in USD.",
        "feed_balance_usd": "Feed balance in USD.", "variance_usd": "Feed minus GL in USD."}},
    "ops_ai_content_sources": {"table": "Synthetic content-source registry for the Affordable Housing Virtual Assistant, with approver and governance status. governed_flag = False indicates an ungoverned source.",
                               "dates": [], "cols": {
        "source_id": "Unique source id.", "assistant_name": "AI assistant name.", "content_source": "Content source the assistant draws on.",
        "source_type": "Type of content source.", "approver": "Who approved the source ('Unapproved' if none).",
        "governed_flag": "True if the source is governed/approved."}},
}


def finalize(sdf, table: str):
    """Cast date columns and attach table/column comments for a generated table."""
    from pyspark.sql import functions as F

    meta = COMMENTS[table]
    for c in meta["dates"]:
        if c in sdf.columns:
            sdf = sdf.withColumn(c, F.col(c).cast("date"))
    for c, cm in meta["cols"].items():
        if c in sdf.columns:
            sdf = sdf.withMetadata(c, {"comment": cm})
    return sdf


def spark_ready(pdf: pd.DataFrame) -> pd.DataFrame:
    """Coerce numpy scalar objects (np.str_, np.int64, np.bool_, ...) that sit in
    object-dtype columns to native Python types so ``spark.createDataFrame`` can
    infer the schema. Python ``date`` values are left untouched.
    """
    df = pdf.copy()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: v.item() if isinstance(v, np.generic) else v)
    return df


def build(spark, pdf: pd.DataFrame):
    """Create a Spark DataFrame from a generated pandas frame (schema-safe)."""
    return spark.createDataFrame(spark_ready(pdf))


def edge(spark, base, upstream_table: str, key: str, upstream_key: str | None = None):
    """Register a Lakeflow dependency edge from ``upstream_table`` onto ``base``.

    Performs a left join against the distinct upstream key so every base row is
    preserved (no cardinality change) while the returned plan references the
    upstream pipeline table — which is what makes the edge render in the graph
    and enforces build ordering.
    """
    from pyspark.sql import functions as F

    upstream_key = upstream_key or key
    up = (
        spark.read.table(upstream_table)
        .select(F.col(upstream_key).alias(key))
        .distinct()
        .withColumn("__edge", F.lit(True))
    )
    return base.join(up, key, "left").drop("__edge")
