from __future__ import annotations

import json

from databricks.sdk.service.iam import User as UserOut
from fastapi import HTTPException

from .core import Dependencies, create_router, logger
from .models import (
    AlertAckIn,
    AlertAckOut,
    AnnotationIn,
    AnnotationOut,
    AnomalyResponse,
    AssistantRequest,
    BriefingResponse,
    EarlyWarningItem,
    EarlyWarningResponse,
    EarlyWarningScoreRequest,
    ExamPackItemIn,
    ExamPackItemOut,
    ExamRequestIn,
    ExamRequestOut,
    Freshness,
    GenieAgentRequest,
    GenieRequest,
    GenieResponse,
    GovernanceInfo,
    GovernedResponse,
    NarrativeRequest,
    Rows,
    VersionOut,
    WatchlistIn,
    WatchlistItemOut,
)
from fastapi.responses import Response, StreamingResponse

from .services import early_warning, gateway, genie, genie_agent, queries
from .services.lakehouse import run_sql

router = create_router()

PERSONA_TITLES = {
    "overview": "the Executive Overview",
    "cio": "Data Governance & Operations (CIO)",
    "cfo": "Finance & Treasury (CFO)",
    "cro": "Credit & Collateral (CRO)",
    "cbo": "Member & Products (CBO)",
    "mission": "Affordable Housing Mission & the $200M pledge",
}


def _rows(ws, cfg, sql: str) -> Rows:
    data = run_sql(ws, cfg.warehouse_id, sql)
    cols = list(data[0].keys()) if data else []
    return Rows(columns=cols, rows=data)


def _user(headers) -> str:
    return headers.user_email or headers.user_name or "demo@fhlb.local"


# --------------------------------------------------------------------------- #
# Meta                                                                          #
# --------------------------------------------------------------------------- #

@router.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@router.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me(user_ws: Dependencies.UserClient):
    return user_ws.current_user.me()


@router.get("/freshness", response_model=Freshness, operation_id="freshness")
def freshness(ws: Dependencies.Client, cfg: Dependencies.Config):
    data = run_sql(ws, cfg.warehouse_id, queries.freshness(cfg))
    return Freshness(as_of=str(data[0]["as_of"]) if data else None)


# --------------------------------------------------------------------------- #
# Overview                                                                      #
# --------------------------------------------------------------------------- #

@router.get("/overview/kpis", response_model=Rows, operation_id="overviewKpis")
def overview_kpis(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.overview_kpis(cfg))


@router.get("/overview/district", response_model=Rows, operation_id="overviewDistrict")
def overview_district(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.overview_district(cfg))


@router.get("/overview/alerts", response_model=Rows, operation_id="overviewAlerts")
def overview_alerts(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.overview_alerts(cfg))


# --------------------------------------------------------------------------- #
# CIO                                                                           #
# --------------------------------------------------------------------------- #

@router.get("/cio/dq-exceptions", response_model=Rows, operation_id="cioDqExceptions")
def cio_dq(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cio_dq_exceptions(cfg))


@router.get("/cio/bi-sla", response_model=Rows, operation_id="cioBiSla")
def cio_bi(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cio_bi_sla(cfg))


@router.get("/cio/dual-run-cost", response_model=Rows, operation_id="cioDualRunCost")
def cio_cost(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cio_dual_run_cost(cfg))


@router.get("/cio/model-backlog", response_model=Rows, operation_id="cioModelBacklog")
def cio_models(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cio_model_backlog(cfg))


@router.get("/cio/access-oob", response_model=Rows, operation_id="cioAccessOob")
def cio_access(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cio_access_oob(cfg))


@router.get("/cio/lineage-fields", response_model=Rows, operation_id="cioLineageFields")
def cio_lineage_fields(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cio_lineage_fields(cfg))


@router.get("/cio/lineage", response_model=Rows, operation_id="cioLineage")
def cio_lineage(ws: Dependencies.Client, cfg: Dependencies.Config, field: str):
    return _rows(ws, cfg, queries.cio_lineage(cfg, field))


# --------------------------------------------------------------------------- #
# CFO                                                                           #
# --------------------------------------------------------------------------- #

@router.get("/cfo/advances-vs-forecast", response_model=Rows, operation_id="cfoAdvancesVsForecast")
def cfo_avf(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cfo_advances_vs_forecast(cfg))


@router.get("/cfo/core-mission-ratio", response_model=Rows, operation_id="cfoCoreMissionRatio")
def cfo_cmr(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cfo_core_mission_ratio(cfg))


@router.get("/cfo/sofr-sensitivity", response_model=Rows, operation_id="cfoSofrSensitivity")
def cfo_sofr(ws: Dependencies.Client, cfg: Dependencies.Config, bps: int = 25):
    return _rows(ws, cfg, queries.cfo_sofr_sensitivity(cfg, bps))


@router.get("/cfo/co-spreads", response_model=Rows, operation_id="cfoCoSpreads")
def cfo_co(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cfo_co_spreads(cfg))


@router.get("/cfo/mbs-unrealized", response_model=Rows, operation_id="cfoMbsUnrealized")
def cfo_mbs(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cfo_mbs_unrealized(cfg))


# --------------------------------------------------------------------------- #
# CRO                                                                           #
# --------------------------------------------------------------------------- #

@router.get("/cro/ratings-overdue", response_model=Rows, operation_id="croRatingsOverdue")
def cro_ratings(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cro_ratings_overdue(cfg))


@router.get("/cro/oc-cushion", response_model=Rows, operation_id="croOcCushion")
def cro_oc(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cro_oc_cushion(cfg))


@router.get("/cro/concentration", response_model=Rows, operation_id="croConcentration")
def cro_conc(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cro_concentration(cfg))


@router.get("/cro/mpf-delinquency", response_model=Rows, operation_id="croMpfDelinquency")
def cro_mpf(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cro_mpf_delinquency(cfg))


# --- Member Early-Warning (credit-risk PD model on Model Serving) --- #

def _ensure_ew_table(db) -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS early_warning_cache ("
        "id INT PRIMARY KEY DEFAULT 1, scan_date DATE NOT NULL, endpoint TEXT, "
        "model_version TEXT, payload JSONB, generated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP)"
    )


def _build_ew_response(items: list[dict], endpoint: str, version: str | None,
                       cached: bool, generated_at: str | None,
                       limit: int | None = None) -> EarlyWarningResponse:
    """Summary counts reflect the FULL scored population; ``items`` may be limited
    to the top-N (by PD) for display."""
    shown = items[:limit] if limit else items
    return EarlyWarningResponse(
        endpoint=endpoint,
        model_version=version,
        generated_at=generated_at,
        cached=cached,
        scored=len(items),
        high=sum(1 for i in items if i.get("risk_band") == "High"),
        elevated=sum(1 for i in items if i.get("risk_band") == "Elevated"),
        rating_gaps=sum(1 for i in items if i.get("rating_gap")),
        items=[EarlyWarningItem(**i) for i in shown],
    )


@router.get("/cro/early-warning", response_model=EarlyWarningResponse, operation_id="croEarlyWarning")
def cro_early_warning(
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
    db: Dependencies.Lakebase,
    limit: int = 25,
    refresh: bool = False,
):
    """Ranked Member Early-Warning board.

    Scores every active member's latest feature snapshot through the credit-risk
    Model Serving endpoint. The full scan is cached same-day in Lakebase so the
    demo panel is instant; ``refresh=true`` forces a fresh scoring pass.
    """
    endpoint = cfg.early_warning_endpoint
    try:
        _ensure_ew_table(db)
        if not refresh:
            rows = db.query(
                "SELECT endpoint, model_version, payload, "
                "to_char(generated_at,'YYYY-MM-DD HH24:MI') AS generated_at "
                "FROM early_warning_cache WHERE id=1 AND scan_date=CURRENT_DATE"
            )
            if rows:
                items = rows[0]["payload"] or []
                return _build_ew_response(
                    items, rows[0]["endpoint"] or endpoint,
                    rows[0]["model_version"], True, rows[0]["generated_at"], limit,
                )
    except Exception:  # noqa: BLE001 - cache is best-effort
        logger.exception("Early-warning cache read failed")

    feature_rows = run_sql(ws, cfg.warehouse_id, queries.cro_early_warning_features(cfg))
    try:
        items = early_warning.score(ws, endpoint, feature_rows)
    except Exception as e:  # noqa: BLE001
        logger.exception("Early-warning scoring failed")
        raise HTTPException(status_code=502, detail=f"Model Serving error: {e}")

    version = early_warning.endpoint_version(ws, endpoint)
    try:
        db.execute(
            "INSERT INTO early_warning_cache (id, scan_date, endpoint, model_version, payload, generated_at) "
            "VALUES (1, CURRENT_DATE, %s, %s, %s::jsonb, CURRENT_TIMESTAMP) "
            "ON CONFLICT (id) DO UPDATE SET scan_date=EXCLUDED.scan_date, endpoint=EXCLUDED.endpoint, "
            "model_version=EXCLUDED.model_version, payload=EXCLUDED.payload, generated_at=EXCLUDED.generated_at",
            (endpoint, version, json.dumps(items, default=str)),
        )
    except Exception:  # noqa: BLE001
        logger.exception("Early-warning cache write failed")

    return _build_ew_response(items, endpoint, version, False, None, limit)


@router.post("/cro/early-warning/score", response_model=EarlyWarningResponse, operation_id="croEarlyWarningScore")
def cro_early_warning_score(
    body: EarlyWarningScoreRequest,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
):
    """Live single-member scoring against the Model Serving endpoint (no cache)."""
    endpoint = cfg.early_warning_endpoint
    feature_rows = run_sql(
        ws, cfg.warehouse_id, queries.cro_early_warning_features(cfg, body.member_id)
    )
    if not feature_rows:
        raise HTTPException(status_code=404, detail="Member not found")
    try:
        items = early_warning.score(ws, endpoint, feature_rows)
    except Exception as e:  # noqa: BLE001
        logger.exception("Early-warning single scoring failed")
        raise HTTPException(status_code=502, detail=f"Model Serving error: {e}")
    version = early_warning.endpoint_version(ws, endpoint)
    return _build_ew_response(items, endpoint, version, False, None)


# --------------------------------------------------------------------------- #
# CBO                                                                           #
# --------------------------------------------------------------------------- #

@router.get("/cbo/utilization", response_model=Rows, operation_id="cboUtilization")
def cbo_util(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cbo_utilization(cfg))


@router.get("/cbo/unused-capacity", response_model=Rows, operation_id="cboUnusedCapacity")
def cbo_unused(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cbo_unused_capacity(cfg))


@router.get("/cbo/mpf-leakage", response_model=Rows, operation_id="cboMpfLeakage")
def cbo_leak(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cbo_mpf_leakage(cfg))


@router.get("/cbo/eadvantage-lurkers", response_model=Rows, operation_id="cboEadvantageLurkers")
def cbo_ea(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cbo_eadvantage_lurkers(cfg))


@router.get("/cbo/prospects", response_model=Rows, operation_id="cboProspects")
def cbo_prospects(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.cbo_prospects(cfg))


# --------------------------------------------------------------------------- #
# Mission                                                                       #
# --------------------------------------------------------------------------- #

@router.get("/mission/pledge", response_model=Rows, operation_id="missionPledge")
def mission_pledge(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.mission_pledge(cfg))


@router.get("/mission/ahp-funnel", response_model=Rows, operation_id="missionAhpFunnel")
def mission_ahp(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.mission_ahp_funnel(cfg))


@router.get("/mission/subsidy-efficiency", response_model=Rows, operation_id="missionSubsidyEfficiency")
def mission_subsidy(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.mission_subsidy_efficiency(cfg))


@router.get("/mission/units-by-tier", response_model=Rows, operation_id="missionUnitsByTier")
def mission_units(ws: Dependencies.Client, cfg: Dependencies.Config):
    return _rows(ws, cfg, queries.mission_units_by_tier(cfg))


# --------------------------------------------------------------------------- #
# Genie                                                                         #
# --------------------------------------------------------------------------- #

@router.post("/genie/{persona}", response_model=GenieResponse, operation_id="genieAsk")
def genie_ask(persona: str, body: GenieRequest, ws: Dependencies.Client, cfg: Dependencies.Config):
    space_id = cfg.genie_space(persona)
    try:
        result = genie.ask(ws, space_id, body.question, body.conversation_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("Genie ask failed")
        raise HTTPException(status_code=502, detail=f"Genie error: {e}")
    return GenieResponse(**result)


@router.get("/genie-viz/{persona}/{conversation_id}/{message_id}/{attachment_id}", operation_id="genieViz")
def genie_viz(
    persona: str,
    conversation_id: str,
    message_id: str,
    attachment_id: str,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
):
    """Proxy the Beta Genie visualization PNG for a query attachment."""
    space_id = cfg.genie_space(persona)
    try:
        png = genie.download_viz(ws, space_id, conversation_id, message_id, attachment_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("Genie viz download failed")
        raise HTTPException(status_code=404, detail=f"Visualization unavailable: {e}")
    if not png:
        raise HTTPException(status_code=404, detail="Visualization unavailable")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "max-age=3600"})


@router.post("/genie-agent/{persona}", operation_id="genieAgentAsk")
def genie_agent_ask(
    persona: str,
    body: GenieAgentRequest,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
):
    """Genie Agent mode (deep research). Streams simplified events as NDJSON so the
    UI can show the agent reasoning, the SQL it runs, and a final cited report."""
    agent_id = cfg.genie_space(persona)

    def gen():
        try:
            for evt in genie_agent.stream(ws, agent_id, body.question, body.conversation_id):
                yield json.dumps(evt) + "\n"
        except Exception as e:  # noqa: BLE001
            logger.exception("Genie agent stream failed")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --------------------------------------------------------------------------- #
# AI Gateway (governed narratives + assistant)                                  #
# --------------------------------------------------------------------------- #

def _write_audit(db, persona, kind, res):
    try:
        db.execute(
            "INSERT INTO ai_narrative_audit (id, persona, kind, endpoint, prompt, response, "
            "guardrail_verdict, request_id, latency_ms) VALUES (gen_random_uuid(), %s,%s,%s,%s,%s,%s,%s,%s)",
            (persona, kind, res["endpoint"], res.get("_prompt", ""), res["content"],
             res["guardrail_verdict"], res.get("request_id"), res.get("latency_ms")),
        )
    except Exception:  # noqa: BLE001 - audit must never break the response
        logger.exception("Failed to write AI audit row")


def _briefing_question(persona: str) -> str:
    """Prompt for the Genie deep-research agent to produce a morning briefing."""
    focus = {
        "overview": "the overall balance sheet, advances, and the most material risks",
        "cfo": "advances, funding mix, core-mission ratio, and margin drivers",
        "cro": "member credit ratings, overdue reviews, and collateral risk concentrations",
        "cbo": "member advance utilization, engagement, and cross-sell opportunities",
        "mission": "affordable housing pledges, AHP disbursements, and mission impact",
        "cio": "data-quality exceptions, pipeline health, and governance/lineage risk",
    }.get(persona, "the most material metrics and risks")
    return (
        f"Write this morning's executive briefing for {PERSONA_TITLES.get(persona, persona)} "
        f"at FHLB Des Moines. Investigate the current data and focus on {focus}. "
        "Produce a crisp, board-ready briefing of 3-4 sentences that cites concrete numbers "
        "with units and calls out the single most important change or risk. "
        "No preamble and no section headers - just the briefing prose."
    )


def _narrative_via_genie_agent(ws, cfg, persona: str) -> dict | None:
    """Generate the briefing with Genie Agent mode; None if unavailable/empty."""
    import time

    space = cfg.genie_space("cfo" if persona == "overview" else persona)
    t0 = time.perf_counter()
    result = genie_agent.run(ws, space, _briefing_question(persona))
    latency = int((time.perf_counter() - t0) * 1000)
    if result.get("error") or not result.get("content"):
        logger.warning("Genie agent briefing unavailable (%s); falling back to gateway",
                        result.get("error"))
        return None
    return {
        "content": result["content"],
        "blocks": result.get("blocks") or None,
        "sources": result.get("sources") or None,
        "endpoint": f"genie-agent:{space}",
        "guardrail_verdict": "Unity Catalog governed",
        "request_id": result.get("conversation_id"),
        "latency_ms": latency,
        "engine": "genie_agent",
        "steps": result.get("steps"),
        "_prompt": f"[narrative:{persona}:genie_agent]",
    }


def _parse_questions(txt: str) -> list[str]:
    """Extract a list of questions from an LLM reply (JSON array or bullet list)."""
    import re

    m = re.search(r"\[.*\]", txt or "", re.S)
    if m:
        try:
            arr = json.loads(m.group(0))
            return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:  # noqa: BLE001
            pass
    out: list[str] = []
    for line in (txt or "").splitlines():
        line = line.strip().lstrip("-*0123456789.) ").strip().strip('",')
        if line.endswith("?") and len(line) > 5:
            out.append(line)
    return out


def _follow_ups(ws, cfg, persona: str, briefing: str) -> list[str]:
    """Suggest 3 data-answerable follow-up questions grounded on the briefing."""
    if not briefing:
        return []
    system = (
        "You suggest follow-up questions for a Databricks Genie analytics assistant that "
        "answers questions over FHLB Des Moines data (advances, members, collateral, credit "
        "ratings, affordable housing, data quality). Given an executive briefing, propose "
        "exactly 3 specific, data-answerable follow-up questions the reader would ask next. "
        "Each must be self-contained, under 14 words, and end with '?'. "
        "Return ONLY a JSON array of 3 strings."
    )
    try:
        res = gateway.chat(ws, cfg.gateway_endpoint, system, briefing, max_tokens=200, temperature=0.4)
        return _parse_questions(res.get("content", ""))[:3]
    except Exception:  # noqa: BLE001 - follow-ups are best-effort
        logger.exception("Follow-up generation failed")
        return []


def _gateway_narrative(ws, cfg, persona: str) -> dict:
    """Generate the briefing with the AI Gateway (Claude), grounded on live KPI facts."""
    facts: dict = {}
    try:
        facts["overview"] = run_sql(ws, cfg.warehouse_id, queries.overview_kpis(cfg))
        if persona == "cio":
            facts["open_exceptions"] = run_sql(ws, cfg.warehouse_id, queries.cio_dq_exceptions(cfg))[:5]
        elif persona == "cfo":
            facts["core_mission_ratio"] = run_sql(ws, cfg.warehouse_id, queries.cfo_core_mission_ratio(cfg))[-4:]
        elif persona == "cro":
            facts["ratings_overdue"] = run_sql(ws, cfg.warehouse_id, queries.cro_ratings_overdue(cfg))[:5]
        elif persona == "cbo":
            facts["utilization"] = run_sql(ws, cfg.warehouse_id, queries.cbo_utilization(cfg))
        elif persona == "mission":
            facts["pledge"] = run_sql(ws, cfg.warehouse_id, queries.mission_pledge(cfg))
    except Exception:  # noqa: BLE001
        logger.exception("Failed gathering narrative facts")

    system = (
        "You are the FHLB Des Moines Executive Command Center briefing writer. "
        "Write a crisp, board-ready briefing of 3-4 sentences for "
        f"{PERSONA_TITLES.get(persona, persona)}. Use ONLY the JSON facts provided. "
        "Cite concrete numbers. Emphasize that data is real-time and AI is governed. "
        "No preamble, no markdown headers."
    )
    user = f"Facts (JSON):\n{json.dumps(facts, default=str)[:6000]}"
    res = gateway.chat(ws, cfg.gateway_endpoint, system, user, max_tokens=320)
    res["_prompt"] = f"[narrative:{persona}]"
    res["engine"] = "gateway"
    return res


def _build_narrative(ws, cfg, persona: str, engine: str) -> dict:
    """Build one briefing for the requested engine, with grounded follow-ups.

    Engine is either the AI Gateway (Claude) grounded on pre-fetched KPI facts, or
    Genie Agent mode (deep research) that investigates the data itself. If Agent mode
    is unavailable, it transparently falls back to the gateway.
    """
    res: dict | None = None
    if engine in ("genie", "genie_agent", "agent"):
        res = _narrative_via_genie_agent(ws, cfg, persona)
    if res is None:
        res = _gateway_narrative(ws, cfg, persona)
    res["follow_ups"] = _follow_ups(ws, cfg, persona, res.get("content", ""))
    return res


@router.post("/ai/narrative", response_model=GovernedResponse, operation_id="aiNarrative")
def ai_narrative(
    body: NarrativeRequest,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
    db: Dependencies.Lakebase,
):
    """Governed executive briefing for a single engine (kept for compatibility)."""
    persona = body.persona
    engine = (body.engine or cfg.briefing_engine or "gateway").lower()
    res = _build_narrative(ws, cfg, persona, engine)
    _write_audit(db, persona, "narrative", res)
    return GovernedResponse(**{k: v for k, v in res.items() if not k.startswith("_")})


def _read_briefings(db, persona: str) -> BriefingResponse:
    rows = db.query(
        "SELECT engine, to_char(scan_date,'YYYY-MM-DD') AS scan_date, payload, "
        "to_char(generated_at,'YYYY-MM-DD HH24:MI') AS generated_at, "
        "(scan_date <> CURRENT_DATE) AS stale "
        "FROM briefing_cache WHERE persona=%s",
        (persona,),
    )
    by = {r["engine"]: r for r in rows}

    def build(key: str) -> tuple[GovernedResponse | None, bool, str | None]:
        r = by.get(key)
        if not r:
            return None, True, None
        try:
            return GovernedResponse(**r["payload"]), bool(r["stale"]), r["generated_at"]
        except Exception:  # noqa: BLE001
            logger.exception("Bad cached briefing payload for %s/%s", persona, key)
            return None, True, None

    gw, gw_stale, gw_at = build("gateway")
    ga, ga_stale, ga_at = build("genie_agent")
    stale = (gw is None or gw_stale) or (ga is None or ga_stale)
    return BriefingResponse(
        persona=persona,
        stale=stale,
        generated_at=gw_at or ga_at,
        gateway=gw,
        genie_agent=ga,
    )


@router.get("/ai/briefings/{persona}", response_model=BriefingResponse, operation_id="getBriefings")
def get_briefings(persona: str, db: Dependencies.Lakebase):
    """Return the cached morning briefing (both engine versions). Fast: no LLM call."""
    try:
        return _read_briefings(db, persona)
    except Exception:  # noqa: BLE001
        logger.exception("Failed reading cached briefings")
        return BriefingResponse(persona=persona, stale=True)


@router.post("/ai/briefings/{persona}", response_model=BriefingResponse, operation_id="runBriefings")
def run_briefings(
    persona: str,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
    db: Dependencies.Lakebase,
):
    """Generate BOTH briefing engines (AI Gateway + Genie deep research) and cache them.

    Expensive path (the Genie agent runs multi-step research), so the UI calls this at
    most once per day per persona or when the user explicitly refreshes; the GET endpoint
    then serves the cached versions instantly and the engine toggle switches between them.
    """
    for engine in ("gateway", "genie_agent"):
        try:
            res = _build_narrative(ws, cfg, persona, engine)
            _write_audit(db, persona, "narrative", res)
            payload = {k: v for k, v in res.items() if not k.startswith("_")}
            db.execute(
                "INSERT INTO briefing_cache (persona, engine, scan_date, payload, generated_at) "
                "VALUES (%s,%s,CURRENT_DATE,%s::jsonb,CURRENT_TIMESTAMP) "
                "ON CONFLICT (persona, engine) DO UPDATE SET scan_date=EXCLUDED.scan_date, "
                "payload=EXCLUDED.payload, generated_at=EXCLUDED.generated_at",
                (persona, engine, json.dumps(payload, default=str)),
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed generating/persisting %s briefing for %s", engine, persona)

    return _read_briefings(db, persona)


@router.post("/ai/assistant", response_model=GovernedResponse, operation_id="aiAssistant")
def ai_assistant(
    body: AssistantRequest,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
    db: Dependencies.Lakebase,
):
    """Governed Affordable Housing Assistant. Answers grounded on approved sources only."""
    sources = run_sql(ws, cfg.warehouse_id, queries.mission_ai_sources(cfg))
    approved = [s for s in sources if s.get("governed_flag")]
    system = (
        "You are the FHLB Des Moines Affordable Housing Program (AHP) Assistant. "
        "You are a GOVERNED assistant: only answer using the approved, governed content "
        "sources listed below. If the question falls outside these sources, say you can only "
        "speak to governed AHP program content and suggest contacting the Community Investment team. "
        "Be concise and helpful.\n\nApproved sources: "
        + json.dumps(approved, default=str)[:3000]
    )
    res = gateway.chat(ws, cfg.gateway_endpoint, system, body.question, max_tokens=400)
    res["_prompt"] = body.question
    _write_audit(db, body.persona, "assistant", res)
    return GovernedResponse(**{k: v for k, v in res.items() if not k.startswith("_")})


@router.get("/ai/governance", response_model=GovernanceInfo, operation_id="aiGovernance")
def ai_governance(ws: Dependencies.Client, cfg: Dependencies.Config, db: Dependencies.Lakebase):
    ep = ws.serving_endpoints.get(cfg.gateway_endpoint)
    ai_gw = ep.ai_gateway
    guardrails = {}
    rate_limits = []
    usage = False
    inference = None
    if ai_gw:
        if ai_gw.guardrails:
            guardrails = ai_gw.guardrails.as_dict()
        if ai_gw.rate_limits:
            rate_limits = [rl.as_dict() for rl in ai_gw.rate_limits]
        if ai_gw.usage_tracking_config:
            usage = bool(ai_gw.usage_tracking_config.enabled)
        if ai_gw.inference_table_config:
            it = ai_gw.inference_table_config
            inference = f"{it.catalog_name}.{it.schema_name}.{it.table_name_prefix}_*"
    sources = run_sql(ws, cfg.warehouse_id, queries.mission_ai_sources(cfg))
    try:
        audit = db.query(
            "SELECT persona, kind, endpoint, guardrail_verdict, latency_ms, "
            "to_char(created_at, 'YYYY-MM-DD HH24:MI') AS created_at "
            "FROM ai_narrative_audit ORDER BY created_at DESC LIMIT 10"
        )
    except Exception:  # noqa: BLE001
        audit = []
    return GovernanceInfo(
        endpoint=cfg.gateway_endpoint,
        guardrails=guardrails,
        rate_limits=rate_limits,
        usage_tracking=usage,
        inference_table=inference,
        content_sources=sources,
        recent_audit=audit,
    )


# --------------------------------------------------------------------------- #
# AI Anomaly Radar (Genie deep-research agent, cached daily in Lakebase)        #
# --------------------------------------------------------------------------- #

_ANOMALY_FOCUS = {
    "overview": "advances, funding, credit concentration, mission delivery, and data quality across the whole Bank",
    "cfo": "advances, funding mix, core-mission ratio, margins, and rate sensitivity",
    "cro": "member credit ratings, overdue reviews, collateral coverage, and borrower concentration",
    "cbo": "member advance utilization, dormant or single-product members, and engagement",
    "mission": "the $200M pledge pace, AHP disbursements, subsidy efficiency, and income-tier mix",
    "cio": "data-quality exceptions, pipeline health, dual-run cost, and lineage/governance gaps",
}


def _anomaly_question(persona: str) -> str:
    focus = _ANOMALY_FOCUS.get(persona, "the most material metrics and risks")
    return (
        f"Act as an anomaly-detection analyst for {PERSONA_TITLES.get(persona, persona)} "
        f"at FHLB Des Moines. Investigate the most recent data and surface the 3-5 most "
        f"important anomalies, outliers, threshold breaches, or areas worth investigating "
        f"right now across {focus}. Look for unusual concentrations, sharp period-over-period "
        f"changes, overdue or past-due items, data-quality issues, and emerging risks. For each "
        f"finding, use a Markdown list item that starts with a bold severity tag - **[High]**, "
        f"**[Medium]**, or **[Low]** - then a short title, then a one-sentence explanation citing "
        f"concrete numbers. Order by materiality. Return only the findings list."
    )


def _anomaly_summary(content: str) -> tuple[str, int, int, int]:
    """Derive a one-line summary + severity counts from the findings markdown."""
    import re

    tags = re.findall(r"\[(high|medium|low)\]", content or "", re.I)
    high = sum(1 for t in tags if t.lower() == "high")
    medium = sum(1 for t in tags if t.lower() == "medium")
    low = sum(1 for t in tags if t.lower() == "low")

    top = ""
    for raw in (content or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*\d.)\s]+", "", line)  # strip list bullet
        line = re.sub(r"\*+", "", line)  # strip bold/italic markers
        line = re.sub(r"\\?\[(high|medium|low)\\?\]", "", line, flags=re.I)  # strip severity tag
        line = re.sub(r"\\?\[\\?\[?\d+\\?\]?\\?\]\([^)]*\)", "", line)  # strip citation links
        line = line.strip(" :-\u2014")
        # Take the title portion (up to an em/en dash or the first sentence).
        title = re.split(r"\s[\u2014\u2013-]\s|\.\s", line, maxsplit=1)[0].strip()
        if len(title) > 4:
            top = title[:90]
            break

    total = high + medium + low
    parts = []
    if high:
        parts.append(f"{high} high")
    if medium:
        parts.append(f"{medium} medium")
    if low:
        parts.append(f"{low} low")
    prefix = " · ".join(parts) if parts else (f"{total} finding{'s' if total != 1 else ''}" if total else "")
    if prefix and top:
        return f"{prefix} — {top}", high, medium, low
    return (top or prefix or "Scan complete"), high, medium, low


def _read_anomaly(db, persona: str) -> AnomalyResponse:
    rows = db.query(
        "SELECT persona, to_char(scan_date,'YYYY-MM-DD') AS scan_date, summary, high, medium, low, "
        "content, blocks, sources, steps, engine, generated_by, "
        "to_char(generated_at,'YYYY-MM-DD HH24:MI') AS generated_at, "
        "(scan_date <> CURRENT_DATE) AS stale "
        "FROM anomaly_scan WHERE persona=%s",
        (persona,),
    )
    if not rows:
        return AnomalyResponse(persona=persona, exists=False, stale=True)
    r = rows[0]
    return AnomalyResponse(
        persona=persona,
        exists=True,
        stale=bool(r["stale"]),
        scan_date=r["scan_date"],
        generated_at=r["generated_at"],
        generated_by=r["generated_by"],
        summary=r["summary"],
        high=r["high"] or 0,
        medium=r["medium"] or 0,
        low=r["low"] or 0,
        content=r["content"] or "",
        blocks=r["blocks"],
        sources=r["sources"],
        steps=r["steps"],
        engine=r["engine"] or "genie_agent",
    )


@router.get("/ai/anomalies/{persona}", response_model=AnomalyResponse, operation_id="getAnomalies")
def get_anomalies(persona: str, db: Dependencies.Lakebase):
    """Return the cached anomaly scan for a persona (empty if never run). Fast: no agent call."""
    try:
        return _read_anomaly(db, persona)
    except Exception:  # noqa: BLE001
        logger.exception("Failed reading cached anomaly scan")
        return AnomalyResponse(persona=persona, exists=False, stale=True)


@router.post("/ai/anomalies/{persona}", response_model=AnomalyResponse, operation_id="runAnomalies")
def run_anomalies(
    persona: str,
    ws: Dependencies.Client,
    cfg: Dependencies.Config,
    db: Dependencies.Lakebase,
    headers: Dependencies.Headers,
):
    """Run the Genie deep-research agent to hunt for anomalies, then cache the result.

    This is the expensive path (multi-step agent research), so the UI only calls it at
    most once per day per persona or when the user explicitly re-scans. The result is
    persisted to Lakebase and served cheaply by the GET endpoint thereafter.
    """
    space = cfg.genie_space("cfo" if persona == "overview" else persona)
    result = genie_agent.run(ws, space, _anomaly_question(persona))
    if result.get("error") or not result.get("content"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error") or "Anomaly scan returned no findings.",
        )

    content = result["content"]
    summary, high, medium, low = _anomaly_summary(content)
    blocks = result.get("blocks") or None
    sources = result.get("sources") or None
    try:
        db.execute(
            "INSERT INTO anomaly_scan (persona, scan_date, summary, high, medium, low, content, "
            "blocks, sources, steps, engine, conversation_id, generated_by, generated_at) "
            "VALUES (%s, CURRENT_DATE, %s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,'genie_agent',%s,%s, CURRENT_TIMESTAMP) "
            "ON CONFLICT (persona) DO UPDATE SET scan_date=EXCLUDED.scan_date, summary=EXCLUDED.summary, "
            "high=EXCLUDED.high, medium=EXCLUDED.medium, low=EXCLUDED.low, content=EXCLUDED.content, "
            "blocks=EXCLUDED.blocks, sources=EXCLUDED.sources, steps=EXCLUDED.steps, "
            "conversation_id=EXCLUDED.conversation_id, generated_by=EXCLUDED.generated_by, "
            "generated_at=EXCLUDED.generated_at",
            (
                persona, summary, high, medium, low, content,
                json.dumps(blocks) if blocks else None,
                json.dumps(sources) if sources else None,
                result.get("steps"), result.get("conversation_id"), _user(headers),
            ),
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist anomaly scan")

    return _read_anomaly(db, persona)


# --------------------------------------------------------------------------- #
# Lakebase: CRO watchlist                                                       #
# --------------------------------------------------------------------------- #

@router.get("/watchlist", response_model=list[WatchlistItemOut], operation_id="listWatchlist")
def list_watchlist(db: Dependencies.Lakebase):
    return db.query(
        "SELECT id, member_id, member_name, reason, severity, added_by, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at "
        "FROM watchlist_item ORDER BY created_at DESC"
    )


@router.post("/watchlist", response_model=WatchlistItemOut, operation_id="addWatchlist")
def add_watchlist(body: WatchlistIn, db: Dependencies.Lakebase, headers: Dependencies.Headers):
    rows = db.query(
        "INSERT INTO watchlist_item (id, member_id, member_name, reason, severity, added_by) "
        "VALUES (gen_random_uuid(), %s,%s,%s,%s,%s) "
        "ON CONFLICT (member_id) DO UPDATE SET reason=EXCLUDED.reason, severity=EXCLUDED.severity "
        "RETURNING id, member_id, member_name, reason, severity, added_by, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at",
        (body.member_id, body.member_name, body.reason, body.severity, _user(headers)),
    )
    return rows[0]


@router.delete("/watchlist/{item_id}", operation_id="removeWatchlist")
def remove_watchlist(item_id: str, db: Dependencies.Lakebase):
    db.execute("DELETE FROM watchlist_item WHERE id=%s", (item_id,))
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Lakebase: alert acknowledgements                                              #
# --------------------------------------------------------------------------- #

@router.get("/alert-acks", response_model=list[AlertAckOut], operation_id="listAlertAcks")
def list_acks(db: Dependencies.Lakebase):
    return db.query(
        "SELECT id, alert_key, persona, acknowledged_by, note, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at FROM alert_ack ORDER BY created_at DESC"
    )


@router.post("/alert-acks", response_model=AlertAckOut, operation_id="ackAlert")
def ack_alert(body: AlertAckIn, db: Dependencies.Lakebase, headers: Dependencies.Headers):
    rows = db.query(
        "INSERT INTO alert_ack (id, alert_key, persona, acknowledged_by, note) "
        "VALUES (gen_random_uuid(), %s,%s,%s,%s) "
        "ON CONFLICT (alert_key) DO UPDATE SET note=EXCLUDED.note, acknowledged_by=EXCLUDED.acknowledged_by "
        "RETURNING id, alert_key, persona, acknowledged_by, note, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at",
        (body.alert_key, body.persona, _user(headers), body.note),
    )
    return rows[0]


# --------------------------------------------------------------------------- #
# Lakebase: CIO examiner evidence packs                                         #
# --------------------------------------------------------------------------- #

@router.get("/exam-requests", response_model=list[ExamRequestOut], operation_id="listExamRequests")
def list_exam_requests(db: Dependencies.Lakebase):
    reqs = db.query(
        "SELECT id, title, examiner, to_char(due_date,'YYYY-MM-DD') AS due_date, status, created_by, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at FROM exam_request ORDER BY created_at DESC"
    )
    for r in reqs:
        r["items"] = db.query(
            "SELECT id, label, source_type, source_ref, "
            "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at "
            "FROM exam_pack_item WHERE exam_request_id=%s ORDER BY created_at",
            (r["id"],),
        )
    return reqs


@router.post("/exam-requests", response_model=ExamRequestOut, operation_id="createExamRequest")
def create_exam_request(body: ExamRequestIn, db: Dependencies.Lakebase, headers: Dependencies.Headers):
    rows = db.query(
        "INSERT INTO exam_request (id, title, examiner, due_date, created_by) "
        "VALUES (gen_random_uuid(), %s,%s,%s,%s) "
        "RETURNING id, title, examiner, to_char(due_date,'YYYY-MM-DD') AS due_date, status, created_by, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at",
        (body.title, body.examiner, body.due_date, _user(headers)),
    )
    rows[0]["items"] = []
    return rows[0]


@router.post("/exam-requests/{req_id}/items", response_model=ExamPackItemOut, operation_id="addExamItem")
def add_exam_item(req_id: str, body: ExamPackItemIn, db: Dependencies.Lakebase):
    rows = db.query(
        "INSERT INTO exam_pack_item (id, exam_request_id, label, source_type, source_ref) "
        "VALUES (gen_random_uuid(), %s,%s,%s,%s) "
        "RETURNING id, label, source_type, source_ref, to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at",
        (req_id, body.label, body.source_type, body.source_ref),
    )
    return rows[0]


# --------------------------------------------------------------------------- #
# Lakebase: annotations                                                         #
# --------------------------------------------------------------------------- #

@router.get("/annotations", response_model=list[AnnotationOut], operation_id="listAnnotations")
def list_annotations(db: Dependencies.Lakebase, persona: str | None = None):
    if persona:
        return db.query(
            "SELECT id, persona, widget_key, author, body, "
            "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at "
            "FROM annotation WHERE persona=%s ORDER BY created_at DESC",
            (persona,),
        )
    return db.query(
        "SELECT id, persona, widget_key, author, body, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at FROM annotation ORDER BY created_at DESC"
    )


@router.post("/annotations", response_model=AnnotationOut, operation_id="addAnnotation")
def add_annotation(body: AnnotationIn, db: Dependencies.Lakebase, headers: Dependencies.Headers):
    rows = db.query(
        "INSERT INTO annotation (id, persona, widget_key, author, body) "
        "VALUES (gen_random_uuid(), %s,%s,%s,%s) "
        "RETURNING id, persona, widget_key, author, body, "
        "to_char(created_at,'YYYY-MM-DD HH24:MI') AS created_at",
        (body.persona, body.widget_key, _user(headers), body.body),
    )
    return rows[0]
