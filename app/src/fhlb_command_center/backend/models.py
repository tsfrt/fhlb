from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --- Generic tabular result (KPIs, charts, tables) --- #

class Rows(BaseModel):
    """Generic query result: a list of row dicts plus the column order."""
    columns: list[str] = []
    rows: list[dict[str, Any]] = []


class Freshness(BaseModel):
    as_of: str | None = None


# --- Genie --- #

class GenieRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class GenieAgentRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class GenieViz(BaseModel):
    title: str | None = None
    attachment_id: str
    message_id: str | None = None


class GenieResponse(BaseModel):
    answer: str
    sql: str | None = None
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    conversation_id: str | None = None
    message_id: str | None = None
    viz: GenieViz | None = None


# --- AI Gateway --- #

class NarrativeRequest(BaseModel):
    persona: str = "overview"
    # Optional per-request override: "gateway" (Claude) or "genie_agent".
    engine: str | None = None


class AssistantRequest(BaseModel):
    question: str
    persona: str = "mission"


class GovernedResponse(BaseModel):
    content: str
    endpoint: str
    guardrail_verdict: str
    request_id: str | None = None
    latency_ms: int | None = None
    engine: str = "gateway"
    steps: int | None = None
    blocks: list[dict[str, Any]] | None = None
    follow_ups: list[str] = []
    sources: list[dict[str, Any]] | None = None


class BriefingResponse(BaseModel):
    """Cached morning briefing for a persona, with both engine versions."""
    persona: str
    stale: bool = True  # true when either engine's cached version is not from today
    generated_at: str | None = None
    gateway: GovernedResponse | None = None
    genie_agent: GovernedResponse | None = None


class AnomalyResponse(BaseModel):
    """Cached AI Anomaly Radar scan for a persona (Genie deep-research agent)."""
    persona: str
    exists: bool = False
    stale: bool = True  # true when the cached scan is not from today
    scan_date: str | None = None
    generated_at: str | None = None
    generated_by: str | None = None
    summary: str | None = None
    high: int = 0
    medium: int = 0
    low: int = 0
    content: str = ""
    blocks: list[dict[str, Any]] | None = None
    sources: list[dict[str, Any]] | None = None
    steps: int | None = None
    engine: str = "genie_agent"


class EarlyWarningDriver(BaseModel):
    feature: str
    label: str
    value: float | None = None
    direction: str
    contribution: float


class EarlyWarningItem(BaseModel):
    member_id: str
    member_name: str
    member_type: str | None = None
    internal_rating: str | None = None
    rating_num: int | None = None
    advances_mm: float | None = None
    pd_12m: float
    risk_band: str
    rating_gap: bool = False
    recommended_action: str
    drivers: list[EarlyWarningDriver] = []


class EarlyWarningScoreRequest(BaseModel):
    member_id: str


class EarlyWarningResponse(BaseModel):
    """Ranked Member Early-Warning board scored by the Model Serving endpoint."""
    endpoint: str
    model_version: str | None = None
    generated_at: str | None = None
    cached: bool = False
    scored: int = 0
    high: int = 0
    elevated: int = 0
    rating_gaps: int = 0
    items: list[EarlyWarningItem] = []


class GovernanceInfo(BaseModel):
    endpoint: str
    guardrails: dict[str, Any] = {}
    rate_limits: list[dict[str, Any]] = []
    usage_tracking: bool = False
    inference_table: str | None = None
    content_sources: list[dict[str, Any]] = []
    recent_audit: list[dict[str, Any]] = []


# --- Lakebase OLTP entities --- #

class WatchlistIn(BaseModel):
    member_id: str
    member_name: str
    reason: str
    severity: str = "medium"


class WatchlistItemOut(BaseModel):
    id: str
    member_id: str
    member_name: str
    reason: str
    severity: str
    added_by: str
    created_at: str


class AlertAckIn(BaseModel):
    alert_key: str
    persona: str
    note: str | None = None


class AlertAckOut(BaseModel):
    id: str
    alert_key: str
    persona: str
    acknowledged_by: str
    note: str | None = None
    created_at: str


class ExamRequestIn(BaseModel):
    title: str
    examiner: str
    due_date: str | None = None


class ExamPackItemIn(BaseModel):
    label: str
    source_type: str
    source_ref: str


class ExamPackItemOut(BaseModel):
    id: str
    label: str
    source_type: str
    source_ref: str
    created_at: str


class ExamRequestOut(BaseModel):
    id: str
    title: str
    examiner: str
    due_date: str | None = None
    status: str
    created_by: str
    created_at: str
    items: list[ExamPackItemOut] = []


class AnnotationIn(BaseModel):
    persona: str
    widget_key: str
    body: str


class AnnotationOut(BaseModel):
    id: str
    persona: str
    widget_key: str
    author: str
    body: str
    created_at: str
