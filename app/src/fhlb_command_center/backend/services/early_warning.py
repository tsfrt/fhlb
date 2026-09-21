"""Member Early-Warning: query the credit-risk PD model on Model Serving.

Assembles the latest per-member feature snapshot (via the SQL warehouse), sends it
to the ``fhlb-member-credit-risk`` serving endpoint, and merges the structured
predictions (pd_12m, risk_band, rating_gap, drivers, action) back with member
identity for the CRO watch board.

The feature contract mirrors ml/early_warning_model.py::FEATURES. The served
pyfunc maps ``member_type`` -> code internally, so the app sends the raw string.
"""
from __future__ import annotations

import json
from typing import Any

from databricks.sdk import WorkspaceClient

from ..core import logger

# Columns the serving signature expects (member_type string + numeric features).
SERVING_FEATURE_KEYS = [
    "member_type",
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
]

_PRED_COLUMNS = ["pd_12m", "risk_band", "rating_gap", "recommended_action", "top_drivers"]


def _record(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row.get(k) for k in SERVING_FEATURE_KEYS}


def _normalize_pred(pred: Any) -> dict[str, Any]:
    """Serving returns records (dicts) for a DataFrame output; tolerate lists too."""
    if isinstance(pred, dict):
        return pred
    if isinstance(pred, (list, tuple)):
        return dict(zip(_PRED_COLUMNS, pred))
    return {}


def score(ws: WorkspaceClient, endpoint: str, feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score member feature rows and return enriched items sorted by PD desc."""
    if not feature_rows:
        return []

    records = [_record(r) for r in feature_rows]
    resp = ws.serving_endpoints.query(name=endpoint, dataframe_records=records)
    preds = resp.predictions or []

    items: list[dict[str, Any]] = []
    for row, raw_pred in zip(feature_rows, preds):
        pred = _normalize_pred(raw_pred)
        drivers_raw = pred.get("top_drivers")
        try:
            drivers = json.loads(drivers_raw) if isinstance(drivers_raw, str) else (drivers_raw or [])
        except (TypeError, ValueError):
            drivers = []
        items.append(
            {
                "member_id": row.get("member_id"),
                "member_name": row.get("member_name"),
                "member_type": row.get("member_type"),
                "internal_rating": row.get("internal_rating"),
                "rating_num": row.get("rating_num"),
                "advances_mm": row.get("advances_mm"),
                "pd_12m": float(pred.get("pd_12m") or 0.0),
                "risk_band": pred.get("risk_band") or "Low",
                "rating_gap": bool(pred.get("rating_gap")),
                "recommended_action": pred.get("recommended_action") or "No action",
                "drivers": drivers,
            }
        )

    items.sort(key=lambda x: x["pd_12m"], reverse=True)
    return items


def endpoint_version(ws: WorkspaceClient, endpoint: str) -> str | None:
    """Best-effort served model version for display/provenance."""
    try:
        ep = ws.serving_endpoints.get(endpoint)
        entities = (ep.config.served_entities if ep.config else None) or []
        for e in entities:
            if getattr(e, "entity_version", None):
                return str(e.entity_version)
    except Exception:  # noqa: BLE001
        logger.exception("Could not read serving endpoint version")
    return None
