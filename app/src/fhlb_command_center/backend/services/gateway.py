"""Governed LLM calls routed through the AI Gateway endpoint (fhlb-governed-llm).

Every call returns the text plus governance metadata (endpoint, guardrail verdict,
request id, latency) so the app can prove how the AI is governed and write an audit row.
"""
from __future__ import annotations

import time
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole


def chat(
    ws: WorkspaceClient,
    endpoint: str,
    system: str,
    user: str,
    max_tokens: int = 400,
    temperature: float = 0.3,
) -> dict[str, Any]:
    start = time.perf_counter()
    resp = ws.serving_endpoints.query(
        name=endpoint,
        messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content=system),
            ChatMessage(role=ChatMessageRole.USER, content=user),
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    content = ""
    if resp.choices:
        msg = resp.choices[0].message
        content = (msg.content if msg else "") or ""

    # Guardrails are enforced by the gateway; PII is masked in/out. If the gateway
    # blocked or masked content we surface that as the verdict.
    verdict = "passed"
    lowered = content.lower()
    if not content:
        verdict = "blocked"
    elif "[redacted]" in lowered or "***" in content:
        verdict = "masked"

    return {
        "content": content,
        "endpoint": endpoint,
        "guardrail_verdict": verdict,
        "request_id": getattr(resp, "id", None),
        "latency_ms": latency_ms,
    }
