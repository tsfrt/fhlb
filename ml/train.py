"""Train + register the Member Early-Warning model to Unity Catalog.

Pulls a per-member feature frame from the lakehouse (SQL Statement Execution API),
trains an XGBoost classifier for 12-month deterioration, wraps it in the shared
``EarlyWarningModel`` pyfunc, and registers it as
``fhlb.des_moines.member_early_warning`` in Unity Catalog.

Run locally against a Databricks profile:

    uv run --with mlflow --with xgboost --with scikit-learn --with pandas \
           --with numpy --with databricks-sdk python ml/train.py
"""
from __future__ import annotations

import json
import os
import tempfile
from importlib.metadata import version

import mlflow
import numpy as np
import pandas as pd
import xgboost as xgb
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from mlflow.models import infer_signature
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import early_warning_model as ewm
from early_warning_model import FEATURES, MEMBER_TYPE_CODES, EarlyWarningModel

CATALOG = "fhlb"
SCHEMA = "des_moines"
WAREHOUSE_ID = os.environ.get("FHLB_WAREHOUSE_ID", "688f49c732cf9083")
MODEL_NAME = f"{CATALOG}.{SCHEMA}.member_early_warning"

FEATURE_SQL = f"""
WITH latest_adv AS (
  SELECT member_id, SUM(outstanding_par_usd) advances
  FROM {CATALOG}.{SCHEMA}.advance_daily_balances
  WHERE business_date=(SELECT MAX(business_date) FROM {CATALOG}.{SCHEMA}.advance_daily_balances)
  GROUP BY member_id
),
total AS (SELECT SUM(advances) t FROM latest_adv),
coll AS (
  SELECT member_id, SUM(lendable_value_usd) lendable
  FROM {CATALOG}.{SCHEMA}.pledged_collateral GROUP BY member_id
),
cr_latest AS (
  SELECT c.* FROM {CATALOG}.{SCHEMA}.call_reports_quarterly c
  JOIN (SELECT member_id, MAX(quarter_end_date) mx
        FROM {CATALOG}.{SCHEMA}.call_reports_quarterly GROUP BY member_id) m
    ON c.member_id=m.member_id AND c.quarter_end_date=m.mx
),
cr_first AS (
  SELECT c.member_id, c.uninsured_deposit_ratio_pct AS uninsured_first
  FROM {CATALOG}.{SCHEMA}.call_reports_quarterly c
  JOIN (SELECT member_id, MIN(quarter_end_date) mn
        FROM {CATALOG}.{SCHEMA}.call_reports_quarterly GROUP BY member_id) m
    ON c.member_id=m.member_id AND c.quarter_end_date=m.mn
),
cr_fed AS (
  SELECT member_id, MAX(CASE WHEN fed_facility_usage_flag THEN 1 ELSE 0 END) fed_recent
  FROM {CATALOG}.{SCHEMA}.call_reports_quarterly GROUP BY member_id
),
rating_latest AS (
  SELECT r.* FROM {CATALOG}.{SCHEMA}.member_credit_ratings r
  JOIN (SELECT member_id, MAX(as_of_date) mx
        FROM {CATALOG}.{SCHEMA}.member_credit_ratings GROUP BY member_id) m
    ON r.member_id=m.member_id AND r.as_of_date=m.mx
)
SELECT
  m.member_id, m.member_name, m.member_type,
  crl.uninsured_deposit_ratio_pct,
  crl.brokered_deposit_growth_pct,
  ROUND(crl.unrealized_securities_loss_usd / NULLIF(crl.total_assets_usd,0) * 100, 3) AS aoci_to_assets_pct,
  crl.tier1_leverage_ratio_pct,
  CAST(SUBSTR(rl.internal_rating,1,1) AS INT) AS rating_num,
  CAST(SUBSTR(rl.prior_rating,1,1) AS INT) AS prior_num,
  DATEDIFF(CURRENT_DATE, rl.next_review_due) AS days_overdue,
  ROUND((coll.lendable - COALESCE(la.advances,0)) / NULLIF(coll.lendable,0) * 100, 2) AS oc_cushion_pct,
  ROUND(COALESCE(la.advances,0) / NULLIF(crl.total_assets_usd,0) * 100, 3) AS advances_to_assets_pct,
  ROUND(COALESCE(la.advances,0) / (SELECT t FROM total) * 100, 4) AS pct_of_book,
  ROUND(LN(GREATEST(m.asset_size_usd, 1)), 4) AS log_assets,
  crf.uninsured_first,
  COALESCE(cf.fed_recent, 0) AS fed_recent,
  ROUND(COALESCE(la.advances,0)/1e6, 1) AS advances_mm,
  rl.internal_rating
FROM {CATALOG}.{SCHEMA}.members m
JOIN cr_latest crl ON crl.member_id=m.member_id
JOIN rating_latest rl ON rl.member_id=m.member_id
LEFT JOIN cr_first crf ON crf.member_id=m.member_id
LEFT JOIN cr_fed cf ON cf.member_id=m.member_id
LEFT JOIN latest_adv la ON la.member_id=m.member_id
LEFT JOIN coll ON coll.member_id=m.member_id
"""


def fetch_frame(ws: WorkspaceClient) -> pd.DataFrame:
    resp = ws.statement_execution.execute_statement(
        statement=FEATURE_SQL, warehouse_id=WAREHOUSE_ID, wait_timeout="50s"
    )
    if resp.status and resp.status.state not in (StatementState.SUCCEEDED, None):
        msg = resp.status.error.message if resp.status.error else str(resp.status.state)
        raise RuntimeError(f"Feature SQL failed: {msg}")
    cols = [c.name for c in resp.manifest.schema.columns]
    types = [c.type_name.value if c.type_name else None for c in resp.manifest.schema.columns]
    numeric = {"INT", "LONG", "SHORT", "BYTE", "FLOAT", "DOUBLE", "DECIMAL"}
    rows = []
    for raw in (resp.result.data_array if resp.result else []) or []:
        rec = {}
        for i, name in enumerate(cols):
            v = raw[i]
            if v is not None and types[i] in numeric:
                v = float(v)
            rec[name] = v
        rows.append(rec)
    return pd.DataFrame(rows)


def make_label(df: pd.DataFrame) -> pd.Series:
    """12-month deterioration proxy from observable trajectory.

    Positive if the member was downgraded, showed Fed-facility usage, or had a
    material rise in uninsured deposits over the observed window.
    """
    downgraded = df["rating_num"] > df["prior_num"]
    fed = df["fed_recent"].fillna(0) >= 1
    uninsured_rise = (
        df["uninsured_deposit_ratio_pct"] - df["uninsured_first"]
    ).fillna(0) >= 8
    return (downgraded | fed | uninsured_rise).astype(int)


def main() -> None:
    ws = WorkspaceClient()
    me = ws.current_user.me().user_name
    print(f"Authenticated as {me}")

    print("Fetching feature frame from lakehouse...")
    df = fetch_frame(ws)
    print(f"Rows: {len(df)}")

    df["member_type_code"] = df["member_type"].map(MEMBER_TYPE_CODES).fillna(-1).astype(int)
    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    y = make_label(df)
    print(f"Positive rate: {y.mean():.3f} ({int(y.sum())}/{len(y)})")

    medians = {c: float(df[c].median()) for c in FEATURES}
    X = df[FEATURES].fillna(medians)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    dtrain = xgb.DMatrix(X_tr.values, label=y_tr.values, feature_names=FEATURES)
    dtest = xgb.DMatrix(X_te.values, label=y_te.values, feature_names=FEATURES)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 4,
        "eta": 0.12,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 3,
        "seed": 42,
    }
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=250,
        evals=[(dtrain, "train"), (dtest, "test")],
        early_stopping_rounds=25,
        verbose_eval=False,
    )
    auc = roc_auc_score(y_te.values, booster.predict(dtest))
    print(f"Test AUC: {auc:.3f}")

    # Band thresholds from the score distribution so bands are populated for the demo.
    all_scores = booster.predict(xgb.DMatrix(X.values, feature_names=FEATURES))
    band_high = float(np.quantile(all_scores, 0.90))
    band_elevated = float(np.quantile(all_scores, 0.65))
    print(f"Bands: elevated>={band_elevated:.3f}  high>={band_high:.3f}")

    meta = {
        "medians": medians,
        "band_high": band_high,
        "band_elevated": band_elevated,
        "features": FEATURES,
        "member_type_codes": MEMBER_TYPE_CODES,
        "auc": auc,
        "positive_rate": float(y.mean()),
        "trained_rows": int(len(df)),
    }

    tmp = tempfile.mkdtemp()
    booster_path = os.path.join(tmp, "booster.json")
    meta_path = os.path.join(tmp, "meta.json")
    booster.save_model(booster_path)
    with open(meta_path, "w") as fh:
        json.dump(meta, fh)

    # Build a live pyfunc instance to validate + infer the serving signature.
    pyfunc = EarlyWarningModel()

    class _Ctx:
        artifacts = {"booster": booster_path, "meta": meta_path}

    pyfunc.load_context(_Ctx())
    sample_in = df.head(5)[["member_type"] + [c for c in FEATURES if c != "member_type_code"]]
    sample_out = pyfunc.predict(None, sample_in)
    print("Sample scored output:\n", sample_out.to_string(index=False))
    signature = infer_signature(sample_in, sample_out)

    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(f"/Users/{me}/fhlb-member-early-warning")

    pip_reqs = [
        f"mlflow=={version('mlflow')}",
        f"xgboost=={version('xgboost')}",
        f"scikit-learn=={version('scikit-learn')}",
        f"pandas=={version('pandas')}",
        f"numpy=={version('numpy')}",
    ]

    with mlflow.start_run(run_name="member-early-warning") as run:
        mlflow.log_params({k: params[k] for k in ("max_depth", "eta", "subsample")})
        mlflow.log_metric("test_auc", auc)
        mlflow.log_metric("positive_rate", float(y.mean()))
        mlflow.log_metric("best_iteration", booster.best_iteration or 0)
        info = mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=pyfunc,
            artifacts={"booster": booster_path, "meta": meta_path},
            code_paths=[ewm.__file__],
            signature=signature,
            input_example=sample_in,
            pip_requirements=pip_reqs,
            registered_model_name=MODEL_NAME,
        )
        print(f"Logged model: {info.model_uri}")
        print(f"Run ID: {run.info.run_id}")

    print(f"Registered {MODEL_NAME}. AUC={auc:.3f}")


if __name__ == "__main__":
    main()
