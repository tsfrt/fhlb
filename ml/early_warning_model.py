"""Member Early-Warning model: shared feature contract + MLflow pyfunc wrapper.

This module is packaged INTO the serving container (via ``code_paths``) so it must
stay dependency-light and self-contained. Both training and inference import the
same ``FEATURES`` list and preprocessing so the model is scored on identical inputs
on the lakehouse (training) and behind Model Serving (inference).

The pyfunc returns an inspectable, structured result -- not a bare 0/1 -- so the
CRO cockpit can show the probability, a risk band, the rating gap, the top drivers
(native XGBoost SHAP contributions), and a recommended action.
"""
from __future__ import annotations

import json
from typing import Any

import mlflow.pyfunc

# --------------------------------------------------------------------------- #
# Feature contract (must match the training + serving SQL in the app)          #
# --------------------------------------------------------------------------- #

# Order matters: the booster is trained on this exact column order.
FEATURES: list[str] = [
    "uninsured_deposit_ratio_pct",
    "brokered_deposit_growth_pct",
    "aoci_to_assets_pct",
    "tier1_leverage_ratio_pct",
    "rating_num",
    "days_overdue",
    "oc_cushion_pct",
    "advances_to_assets_pct",
    "pct_of_book",
    "log_assets",
    "member_type_code",
]

# member_type string -> ordinal code (fixed so train == serve).
MEMBER_TYPE_CODES: dict[str, int] = {
    "Commercial Bank": 0,
    "Credit Union": 1,
    "Thrift": 2,
    "Insurance Company": 3,
    "CDFI": 4,
}

# Human-readable driver labels and whether a higher value is worse (for prose).
FEATURE_LABELS: dict[str, str] = {
    "uninsured_deposit_ratio_pct": "Uninsured deposit ratio",
    "brokered_deposit_growth_pct": "Brokered deposit growth",
    "aoci_to_assets_pct": "Unrealized securities loss / assets",
    "tier1_leverage_ratio_pct": "Tier 1 leverage ratio",
    "rating_num": "Internal credit rating",
    "days_overdue": "Days past review cadence",
    "oc_cushion_pct": "Collateral (OC) cushion",
    "advances_to_assets_pct": "Advances / assets",
    "pct_of_book": "Share of advance book",
    "log_assets": "Asset size",
    "member_type_code": "Member type",
}


def prep_frame(model_input: Any) -> "Any":
    """Coerce a records list / DataFrame into the model's numeric feature matrix.

    Kept import-light: pandas is imported lazily so this module can be introspected
    without the full ML stack.
    """
    import numpy as np
    import pandas as pd

    if not isinstance(model_input, pd.DataFrame):
        model_input = pd.DataFrame(model_input)
    df = model_input.copy()

    # Map member_type -> code if a raw string column was passed instead of the code.
    if "member_type_code" not in df.columns and "member_type" in df.columns:
        df["member_type_code"] = (
            df["member_type"].map(MEMBER_TYPE_CODES).fillna(-1).astype(int)
        )

    for col in FEATURES:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[FEATURES]


def _band(prob: float, high: float, elevated: float) -> str:
    if prob >= high:
        return "High"
    if prob >= elevated:
        return "Elevated"
    return "Low"


def _action(band: str, rating_gap: bool) -> str:
    if band == "High" and rating_gap:
        return "Accelerate credit review; add to watchlist"
    if band == "High":
        return "Add to watchlist; verify collateral coverage"
    if band == "Elevated":
        return "Monitor; schedule interim review"
    return "No action"


class EarlyWarningModel(mlflow.pyfunc.PythonModel):
    """Serves the XGBoost booster with structured, explainable output."""

    def load_context(self, context):  # noqa: D401
        import xgboost as xgb

        self._booster = xgb.Booster()
        self._booster.load_model(context.artifacts["booster"])
        with open(context.artifacts["meta"]) as fh:
            self._meta = json.load(fh)
        self._medians: dict[str, float] = self._meta.get("medians", {})
        self._high: float = float(self._meta.get("band_high", 0.5))
        self._elevated: float = float(self._meta.get("band_elevated", 0.25))

    def _fill(self, feat):
        import pandas as pd  # noqa: F401

        for col in FEATURES:
            med = self._medians.get(col, 0.0)
            feat[col] = feat[col].fillna(med)
        return feat

    def predict(self, context, model_input, params=None):
        import numpy as np
        import pandas as pd
        import xgboost as xgb

        feat = self._fill(prep_frame(model_input))
        dmat = xgb.DMatrix(feat.values, feature_names=FEATURES)
        probs = self._booster.predict(dmat)
        # Native SHAP: last column is the bias term.
        contribs = self._booster.predict(dmat, pred_contribs=True)

        out: list[dict[str, Any]] = []
        for i in range(len(feat)):
            prob = float(probs[i])
            row = feat.iloc[i]
            rating_num = float(row.get("rating_num", 3) or 3)
            band = _band(prob, self._high, self._elevated)
            rating_gap = bool(band == "High" and rating_num <= 2)

            row_contribs = contribs[i][:-1]  # drop bias
            order = np.argsort(np.abs(row_contribs))[::-1][:3]
            drivers = []
            for j in order:
                c = float(row_contribs[j])
                fname = FEATURES[j]
                drivers.append(
                    {
                        "feature": fname,
                        "label": FEATURE_LABELS.get(fname, fname),
                        "value": (None if pd.isna(row[fname]) else float(row[fname])),
                        "direction": "increases risk" if c >= 0 else "reduces risk",
                        "contribution": round(c, 4),
                    }
                )

            out.append(
                {
                    "pd_12m": round(prob, 4),
                    "risk_band": band,
                    "rating_gap": rating_gap,
                    "recommended_action": _action(band, rating_gap),
                    "top_drivers": json.dumps(drivers),
                }
            )

        return pd.DataFrame(out)
