# Member Early-Warning model (Model Serving)

A tabular ML model that ranks FHLB member institutions by their probability of
**12-month credit deterioration** and serves it behind a Databricks Model Serving
endpoint. The CRO cockpit calls the endpoint to show a ranked watch board, the
rating gap (High PD but still rated Strong/Satisfactory), and the top drivers.

This is the classical-ML counterpart to the app's governed LLM (AI Gateway) and
Genie deep-research agent: a versioned model in Unity Catalog, served as an API.

## Artifacts

| File | Purpose |
|------|---------|
| `early_warning_model.py` | Shared feature contract + MLflow pyfunc (packaged into serving) |
| `train.py` | Pull features from the lakehouse, train XGBoost, register to UC |
| `deploy_serving.py` | Create/update the `fhlb-member-credit-risk` serving endpoint |
| `validate_model.py` | Prepare a labeled holdout dataset and validate the **deployed** endpoint |

## Model

- **Target:** binary 12-month deterioration proxy (rating downgrade, Fed-facility
  usage, or a material rise in uninsured deposits over the observed window).
- **Features:** latest call-report metrics (uninsured deposit ratio, brokered
  growth, AOCI/assets, Tier 1 leverage), internal rating, days past review
  cadence, OC cushion, advances/assets, share of book, asset size, member type.
- **Output (structured):** `pd_12m`, `risk_band` (Low/Elevated/High),
  `rating_gap`, `recommended_action`, and `top_drivers` (native XGBoost SHAP
  contributions) so the score is inspectable rather than a black box.

## Run

```bash
export DATABRICKS_CONFIG_PROFILE=fevm-serverless-stable-blj52t

# 1. Train + register fhlb.des_moines.member_early_warning
uv run --with mlflow --with xgboost --with scikit-learn --with pandas \
       --with numpy --with databricks-sdk python ml/train.py

# 2. Deploy / update the fhlb-member-credit-risk serving endpoint
uv run --with mlflow --with databricks-sdk python ml/deploy_serving.py

# 3. Validate the deployed endpoint (prepares a dataset + runs checks)
uv run --with mlflow --with "mlflow[databricks]" --with xgboost \
       --with scikit-learn --with pandas --with numpy --with matplotlib \
       --with databricks-sdk python ml/validate_model.py
```

The app reads the endpoint name from `FHLB_COMMAND_CENTER_EARLY_WARNING_ENDPOINT`
(wired as a bundle serving-endpoint resource in `app/databricks.yml`).

## Validation

`validate_model.py` prepares a labeled validation dataset and scores it through the
**live** Model Serving endpoint (not just a local artifact), so it validates exactly
what production calls.

- **Dataset:** the full member feature frame from the lakehouse (same `FEATURES`
  contract and 12-month deterioration proxy label as training), then the *identical*
  25% stratified holdout the booster never trained on (`random_state=42`). Raw
  features are sent with nulls preserved to exercise the endpoint's own imputation.
- **Checks:** discrimination (ROC-AUC, PR-AUC, KS), calibration (Brier + reliability
  curve), threshold metrics at the model's own Elevated/High band cutoffs, band
  monotonicity, output-contract conformance, missing-value robustness, train/serve
  parity (endpoint PD vs registered UC model PD), and p50/p95 latency.
- **Gates (must pass):** AUC ≥ 0.70, AUC drop vs training ≤ 0.10, Brier ≤ 0.25,
  monotonic band PD, valid output contract, null robustness, parity |Δ| ≤ 1e-6.
- **Outputs:** an MLflow run (metrics + ROC/calibration/separation plots + the scored
  dataset) under `/Users/<you>/fhlb-member-early-warning-validation`, plus local
  copies in `ml/artifacts/` (`validation_dataset.{parquet,csv}`,
  `validation_scorecard.json`). Exits non-zero if any gate fails (CI-friendly).

Latest run (endpoint v2, 313-member out-of-sample holdout): **PASS** — ROC-AUC 0.847,
PR-AUC 0.843, KS 0.541, Brier 0.157, High-band precision 1.00, train/serve parity 0.0,
p50 121 ms.
