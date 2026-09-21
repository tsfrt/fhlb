"""Validate the deployed Member Early-Warning credit-risk model.

Prepares a labeled validation dataset from the lakehouse (the same feature contract
and 12-month deterioration proxy label used in training), scores it through the LIVE
Model Serving endpoint ``fhlb-member-credit-risk``, and runs a battery of validation
checks against the *deployed* model — not just a local artifact:

  * Discrimination     -- ROC-AUC, PR-AUC, KS on the 25% out-of-sample holdout
  * Calibration        -- Brier score + reliability curve
  * Threshold metrics  -- precision / recall / F1 / confusion matrix at the model's
                          own Elevated & High band cutoffs (read from meta.json)
  * Band behavior      -- population mix + monotonic mean-PD across Low/Elevated/High
  * Output contract    -- required fields, PD in [0,1], valid bands, parseable drivers
  * Robustness         -- a row with missing features still returns a valid score
  * Train/serve parity -- endpoint PD == registered UC model PD (bit-for-bit)
  * Latency            -- p50 / p95 single-row round-trip

Everything is logged to an MLflow run (metrics, plots, the scored dataset, and a
PASS/FAIL scorecard) so the validation is governed and reproducible.

Run against a Databricks profile:

    export DATABRICKS_CONFIG_PROFILE=fevm-serverless-stable-blj52t
    uv run --with mlflow --with xgboost --with scikit-learn --with pandas \
           --with numpy --with matplotlib --with databricks-sdk \
           python ml/validate_model.py
"""
from __future__ import annotations

import glob
import json
import os
import tempfile
import time
from typing import Any

import numpy as np
import pandas as pd
from databricks.sdk import WorkspaceClient
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

# Reuse the exact feature SQL, label logic, and feature contract from training so
# validation is scored on identical inputs to what the model expects.
import train  # noqa: E402  (local module)
from early_warning_model import FEATURES  # noqa: E402

MODEL_NAME = "fhlb.des_moines.member_early_warning"
ENDPOINT_NAME = os.environ.get("FHLB_EARLY_WARNING_ENDPOINT", "fhlb-member-credit-risk")

# Features the serving signature expects (member_type string + numeric; the pyfunc
# derives member_type_code internally, so we never send it).
SERVE_KEYS = ["member_type"] + [c for c in FEATURES if c != "member_type_code"]

# ---- Validation gates (hard thresholds the deployed model must clear) --------- #
GATE_MIN_AUC = 0.70          # holdout discrimination floor
GATE_MAX_AUC_DROP = 0.10     # holdout AUC may not fall > this below training AUC
GATE_MAX_BRIER = 0.25        # calibration ceiling (0.25 == uninformative for p=.5)
GATE_MAX_PARITY_DIFF = 1e-6  # endpoint vs registered model PD agreement


def to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """JSON-safe records (np scalars -> native, NaN -> None) for the serving call."""
    recs: list[dict[str, Any]] = []
    for _, r in frame.iterrows():
        rec: dict[str, Any] = {}
        for c in frame.columns:
            v = r[c]
            if isinstance(v, float) and pd.isna(v):
                rec[c] = None
            elif v is None:
                rec[c] = None
            elif isinstance(v, np.integer):
                rec[c] = int(v)
            elif isinstance(v, np.floating):
                rec[c] = None if np.isnan(v) else float(v)
            else:
                rec[c] = v
        recs.append(rec)
    return recs


def query_endpoint(
    ws: WorkspaceClient, records: list[dict[str, Any]], retries: int = 12
) -> list[dict[str, Any]]:
    """Query the endpoint, tolerating scale-to-zero cold starts."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = ws.serving_endpoints.query(name=ENDPOINT_NAME, dataframe_records=records)
            preds = resp.predictions or []
            return [p if isinstance(p, dict) else dict(p) for p in preds]
        except Exception as e:  # noqa: BLE001
            last_err = e
            wait = min(30, 5 + attempt * 5)
            print(f"  endpoint not ready (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"Endpoint {ENDPOINT_NAME} did not respond: {last_err}")


def ks_statistic(y_true: np.ndarray, scores: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, scores)
    return float(np.max(tpr - fpr))


def threshold_metrics(y_true: np.ndarray, scores: np.ndarray, thr: float) -> dict[str, Any]:
    pred = (scores >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "threshold": round(float(thr), 4),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "flagged": int(pred.sum()),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def make_plots(out_dir: str, y_true: np.ndarray, scores: np.ndarray, band_high: float) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve

    paths: list[str] = []

    # ROC
    fpr, tpr, _ = roc_curve(y_true, scores)
    auc = roc_auc_score(y_true, scores)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot(fpr, tpr, color="#2563eb", label=f"AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="#94a3b8")
    ax.set(xlabel="False positive rate", ylabel="True positive rate", title="ROC — holdout")
    ax.legend(loc="lower right")
    p = os.path.join(out_dir, "roc_curve.png")
    fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # Calibration
    frac_pos, mean_pred = calibration_curve(y_true, scores, n_bins=8, strategy="quantile")
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.plot(mean_pred, frac_pos, "o-", color="#2563eb", label="Model")
    ax.plot([0, 1], [0, 1], "--", color="#94a3b8", label="Perfect")
    ax.set(xlabel="Mean predicted PD", ylabel="Observed rate", title="Calibration — holdout")
    ax.legend(loc="upper left")
    p = os.path.join(out_dir, "calibration.png")
    fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # PD distribution by label
    fig, ax = plt.subplots(figsize=(4.5, 4))
    bins = np.linspace(0, 1, 21)
    ax.hist(scores[y_true == 0], bins=bins, alpha=0.6, label="No deterioration", color="#22c55e")
    ax.hist(scores[y_true == 1], bins=bins, alpha=0.6, label="Deterioration", color="#ef4444")
    ax.axvline(band_high, color="#111827", ls="--", lw=1, label=f"High cutoff {band_high:.2f}")
    ax.set(xlabel="Predicted PD (12m)", ylabel="Members", title="Score separation")
    ax.legend()
    p = os.path.join(out_dir, "pd_distribution.png")
    fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    return paths


def main() -> None:
    ws = WorkspaceClient()
    me = ws.current_user.me().user_name
    print(f"Authenticated as {me}")

    # ---- Provenance: which version is actually serving? ---------------------- #
    ep = ws.serving_endpoints.get(ENDPOINT_NAME)
    served_version = None
    for e in (ep.config.served_entities if ep.config else []) or []:
        if getattr(e, "entity_version", None):
            served_version = str(e.entity_version)
    print(f"Endpoint {ENDPOINT_NAME} serving {MODEL_NAME} v{served_version}")

    # ---- Pull the model artifacts once (meta thresholds + parity check) ------ #
    import mlflow

    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    model_uri = f"models:/{MODEL_NAME}/{served_version}" if served_version else f"models:/{MODEL_NAME}@latest"
    print(f"Downloading model artifacts from {model_uri} ...")
    local_model = mlflow.artifacts.download_artifacts(artifact_uri=model_uri)
    meta = {}
    meta_files = glob.glob(os.path.join(local_model, "**", "meta.json"), recursive=True)
    if meta_files:
        with open(meta_files[0]) as fh:
            meta = json.load(fh)
    band_high = float(meta.get("band_high", 0.5))
    band_elevated = float(meta.get("band_elevated", 0.25))
    train_auc = float(meta["auc"]) if "auc" in meta else None
    print(f"Bands: elevated>={band_elevated:.3f} high>={band_high:.3f} | training AUC={train_auc}")

    # ---- Prepare the validation dataset (identical contract to training) ----- #
    print("Fetching feature frame from lakehouse...")
    df = train.fetch_frame(ws)
    for col in FEATURES:
        if col != "member_type_code":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["member_type_code"] = df["member_type"].map(train.MEMBER_TYPE_CODES).fillna(-1).astype(int)
    y = train.make_label(df).to_numpy()
    print(f"Population: {len(df)} members | positive rate {y.mean():.3f}")

    # Reproduce the training holdout EXACTLY (same fill, seed, stratify) so the
    # deployed model is judged on rows it never saw during training.
    medians = {c: float(df[c].median()) for c in FEATURES}
    X = df[FEATURES].fillna(medians)
    _, X_te, _, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    hold_idx = X_te.index
    holdout = df.loc[hold_idx].reset_index(drop=True)
    y_te = np.asarray(y_te)
    print(f"Holdout (out-of-sample): {len(holdout)} members | positive rate {y_te.mean():.3f}")

    # Send RAW features (NaNs preserved) so we validate the endpoint's imputation.
    records = to_records(holdout[SERVE_KEYS])
    print(f"Scoring {len(records)} holdout members through the live endpoint...")
    t0 = time.time()
    preds = query_endpoint(ws, records)
    batch_ms = (time.time() - t0) * 1000
    if len(preds) != len(records):
        raise RuntimeError(f"Endpoint returned {len(preds)} predictions for {len(records)} rows")

    scored = pd.DataFrame(preds)
    scores = pd.to_numeric(scored["pd_12m"], errors="coerce").to_numpy()

    # ---- Latency (single-row round trips) ----------------------------------- #
    one = to_records(holdout[SERVE_KEYS].head(1))
    lat = []
    for _ in range(15):
        s = time.time()
        query_endpoint(ws, one, retries=2)
        lat.append((time.time() - s) * 1000)
    p50, p95 = float(np.percentile(lat, 50)), float(np.percentile(lat, 95))

    # ---- Core metrics -------------------------------------------------------- #
    auc = float(roc_auc_score(y_te, scores))
    pr_auc = float(average_precision_score(y_te, scores))
    brier = float(brier_score_loss(y_te, scores))
    ks = ks_statistic(y_te, scores)
    tm_high = threshold_metrics(y_te, scores, band_high)
    tm_elev = threshold_metrics(y_te, scores, band_elevated)

    # ---- Band behavior ------------------------------------------------------- #
    band = scored["risk_band"].astype(str)
    band_tbl = {}
    for b in ["Low", "Elevated", "High"]:
        mask = (band == b).to_numpy()
        band_tbl[b] = {
            "n": int(mask.sum()),
            "share": round(float(mask.mean()), 4),
            "mean_pd": round(float(np.nanmean(scores[mask])), 4) if mask.any() else None,
            "actual_rate": round(float(y_te[mask].mean()), 4) if mask.any() else None,
        }
    present = [b for b in ["Low", "Elevated", "High"] if band_tbl[b]["mean_pd"] is not None]
    band_monotonic = all(
        band_tbl[present[i]]["mean_pd"] <= band_tbl[present[i + 1]]["mean_pd"]
        for i in range(len(present) - 1)
    )

    # ---- Output contract ----------------------------------------------------- #
    required = ["pd_12m", "risk_band", "rating_gap", "recommended_action", "top_drivers"]
    fields_ok = all(c in scored.columns for c in required)
    pd_in_range = bool(np.all((scores >= 0) & (scores <= 1)) and not np.any(np.isnan(scores)))
    bands_valid = bool(set(band.unique()) <= {"Low", "Elevated", "High"})
    drivers_ok = True
    for d in scored["top_drivers"].tolist():
        try:
            parsed = json.loads(d) if isinstance(d, str) else d
            drivers_ok = drivers_ok and isinstance(parsed, list) and len(parsed) >= 1
        except (TypeError, ValueError):
            drivers_ok = False
    contract_ok = fields_ok and pd_in_range and bands_valid and drivers_ok

    # ---- Robustness: a row with missing inputs still scores ------------------ #
    stress = holdout[SERVE_KEYS].head(1).copy()
    for c in ["uninsured_deposit_ratio_pct", "tier1_leverage_ratio_pct", "oc_cushion_pct"]:
        stress[c] = np.nan
    try:
        rp = query_endpoint(ws, to_records(stress), retries=3)[0]
        rv = float(rp.get("pd_12m"))
        robustness_ok = 0.0 <= rv <= 1.0 and str(rp.get("risk_band")) in {"Low", "Elevated", "High"}
    except Exception as e:  # noqa: BLE001
        print(f"  robustness check error: {e}")
        robustness_ok = False

    # ---- Train/serve parity: endpoint vs registered UC model ----------------- #
    parity_diff = None
    try:
        local_pyfunc = mlflow.pyfunc.load_model(local_model)
        sample = holdout[SERVE_KEYS].head(min(50, len(holdout)))
        local_out = local_pyfunc.predict(sample)
        local_pd = pd.to_numeric(local_out["pd_12m"], errors="coerce").to_numpy()
        endp_pd = scores[: len(local_pd)]
        parity_diff = float(np.max(np.abs(local_pd - endp_pd)))
    except Exception as e:  # noqa: BLE001
        print(f"  parity check skipped: {e}")

    # ---- Gates / scorecard --------------------------------------------------- #
    gates: dict[str, dict[str, Any]] = {
        "auc_floor": {"value": round(auc, 4), "min": GATE_MIN_AUC, "pass": auc >= GATE_MIN_AUC},
        "brier_ceiling": {"value": round(brier, 4), "max": GATE_MAX_BRIER, "pass": brier <= GATE_MAX_BRIER},
        "band_monotonic": {"value": band_monotonic, "pass": bool(band_monotonic)},
        "output_contract": {"value": contract_ok, "pass": bool(contract_ok)},
        "null_robustness": {"value": robustness_ok, "pass": bool(robustness_ok)},
    }
    if train_auc is not None:
        drop = train_auc - auc
        gates["auc_stability"] = {
            "value": round(drop, 4), "max_drop": GATE_MAX_AUC_DROP, "pass": drop <= GATE_MAX_AUC_DROP,
        }
    if parity_diff is not None:
        gates["train_serve_parity"] = {
            "value": parity_diff, "max": GATE_MAX_PARITY_DIFF, "pass": parity_diff <= GATE_MAX_PARITY_DIFF,
        }
    overall_pass = all(g["pass"] for g in gates.values())

    scorecard = {
        "model": MODEL_NAME,
        "endpoint": ENDPOINT_NAME,
        "served_version": served_version,
        "validated_by": me,
        "validated_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "population_rows": int(len(df)),
        "holdout_rows": int(len(holdout)),
        "holdout_positive_rate": round(float(y_te.mean()), 4),
        "metrics": {
            "roc_auc": round(auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier": round(brier, 4),
            "ks": round(ks, 4),
            "training_auc": train_auc,
            "at_high_cutoff": tm_high,
            "at_elevated_cutoff": tm_elev,
        },
        "bands": band_tbl,
        "latency_ms": {"batch_all": round(batch_ms, 1), "p50": round(p50, 1), "p95": round(p95, 1)},
        "parity_max_abs_diff": parity_diff,
        "gates": gates,
        "overall": "PASS" if overall_pass else "FAIL",
    }

    # ---- Persist dataset + report ------------------------------------------- #
    art_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
    os.makedirs(art_dir, exist_ok=True)
    ds = holdout.copy()
    ds["label_deterioration_12m"] = y_te
    ds["pred_pd_12m"] = scores
    ds["pred_risk_band"] = scored["risk_band"].to_numpy()
    ds["pred_rating_gap"] = scored["rating_gap"].to_numpy()
    ds_path = os.path.join(art_dir, "validation_dataset.parquet")
    ds.to_parquet(ds_path, index=False)
    ds.to_csv(os.path.join(art_dir, "validation_dataset.csv"), index=False)
    card_path = os.path.join(art_dir, "validation_scorecard.json")
    with open(card_path, "w") as fh:
        json.dump(scorecard, fh, indent=2)

    # ---- Log to MLflow ------------------------------------------------------- #
    mlflow.set_experiment(f"/Users/{me}/fhlb-member-early-warning-validation")
    with tempfile.TemporaryDirectory() as tmp:
        plots = make_plots(tmp, y_te, scores, band_high)
        with mlflow.start_run(run_name=f"validation-v{served_version}") as run:
            mlflow.set_tags({
                "model": MODEL_NAME,
                "endpoint": ENDPOINT_NAME,
                "served_version": served_version or "unknown",
                "validation.result": scorecard["overall"],
            })
            mlflow.log_metrics({
                "roc_auc": auc,
                "pr_auc": pr_auc,
                "brier": brier,
                "ks": ks,
                "high_precision": tm_high["precision"],
                "high_recall": tm_high["recall"],
                "high_f1": tm_high["f1"],
                "elevated_recall": tm_elev["recall"],
                "latency_p50_ms": p50,
                "latency_p95_ms": p95,
                "holdout_rows": len(holdout),
                "holdout_positive_rate": float(y_te.mean()),
                **({"parity_max_abs_diff": parity_diff} if parity_diff is not None else {}),
                **({"auc_drop_vs_training": train_auc - auc} if train_auc is not None else {}),
            })
            for p in plots:
                mlflow.log_artifact(p, artifact_path="plots")
            mlflow.log_artifact(card_path, artifact_path="report")
            mlflow.log_artifact(ds_path, artifact_path="dataset")
            run_id = run.info.run_id

    # ---- Console scorecard --------------------------------------------------- #
    print("\n" + "=" * 66)
    print(f"  MEMBER EARLY-WARNING — MODEL VALIDATION  [{scorecard['overall']}]")
    print("=" * 66)
    print(f"  Endpoint         {ENDPOINT_NAME}  (v{served_version})")
    print(f"  Holdout          {len(holdout)} members, {y_te.mean():.1%} positive (out-of-sample)")
    print(f"  ROC-AUC          {auc:.3f}   (training {train_auc})")
    print(f"  PR-AUC           {pr_auc:.3f}")
    print(f"  KS               {ks:.3f}")
    print(f"  Brier            {brier:.3f}")
    print(f"  High cutoff      thr={band_high:.3f}  P={tm_high['precision']:.2f} "
          f"R={tm_high['recall']:.2f} F1={tm_high['f1']:.2f}  flagged={tm_high['flagged']}")
    print(f"  Elevated cutoff  thr={band_elevated:.3f}  R={tm_elev['recall']:.2f}")
    print("  Bands            " + "  ".join(
        f"{b}:{band_tbl[b]['n']}({band_tbl[b]['mean_pd']})" for b in ["Low", "Elevated", "High"]
    ))
    print(f"  Parity           max|Δ|={parity_diff}")
    print(f"  Latency          p50={p50:.0f}ms p95={p95:.0f}ms")
    print("-" * 66)
    for name, g in gates.items():
        flag = "PASS" if g["pass"] else "FAIL"
        print(f"  [{flag}]  {name:<20} {g.get('value')}")
    print("-" * 66)
    print(f"  Dataset          {ds_path}")
    print(f"  Scorecard        {card_path}")
    print(f"  MLflow run       {run_id}")
    print("=" * 66)

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
