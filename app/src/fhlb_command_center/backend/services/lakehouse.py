"""Lakehouse access via the Databricks SQL Statement Execution API (SDK-native)."""
from __future__ import annotations

from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

_NUMERIC = {"INT", "LONG", "SHORT", "BYTE", "FLOAT", "DOUBLE", "DECIMAL"}


def _cast(value: Any, type_name: str | None) -> Any:
    if value is None:
        return None
    if type_name in _NUMERIC:
        try:
            f = float(value)
            return int(f) if f.is_integer() else f
        except (TypeError, ValueError):
            return value
    return value


def run_sql(ws: WorkspaceClient, warehouse_id: str, statement: str) -> list[dict[str, Any]]:
    """Execute a SQL statement and return rows as a list of typed dicts."""
    resp = ws.statement_execution.execute_statement(
        statement=statement,
        warehouse_id=warehouse_id,
        wait_timeout="50s",
    )
    if resp.status and resp.status.state not in (StatementState.SUCCEEDED, None):
        msg = resp.status.error.message if resp.status.error else str(resp.status.state)
        raise RuntimeError(f"SQL failed: {msg}")

    manifest = resp.manifest
    cols = (manifest.schema.columns if manifest and manifest.schema else None) or []
    names = [c.name or "" for c in cols]
    types = [c.type_name.value if c.type_name else None for c in cols]

    rows: list[dict[str, Any]] = []
    data = resp.result.data_array if resp.result else None
    for raw in data or []:
        rows.append({names[i]: _cast(raw[i], types[i]) for i in range(len(names))})
    return rows
