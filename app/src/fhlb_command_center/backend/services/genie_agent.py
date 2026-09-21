"""Genie Agent mode (deep research) via the Agent mode SSE API.

Agent mode runs multi-step research: it plans, runs several SQL queries, iterates on
the results, and returns a cited report. We proxy the upstream Server-Sent Events
stream into a simplified sequence of dict events the frontend can render live:

    {"type": "created",   "conversation_id": "..."}
    {"type": "reasoning", "text": "..."}
    {"type": "query",     "title": "...", "sql": "..."}
    {"type": "report",    "blocks": [{"kind": "text"|"table", ...}]}
    {"type": "done"}
    {"type": "error",     "message": "..."}

Docs: https://docs.databricks.com/aws/en/genie-agents/api (Beta; a workspace admin
must enable "Agent Mode APIs for Genie Agents" under Previews).
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterator

import requests
from databricks.sdk import WorkspaceClient

from ..core import logger

# Inline citations look like ``\[[1](https://.../gra_focus=<query_id>)\]``. We turn
# them into clean, clickable Markdown links whose visible text is ``[1]`` (brackets
# escaped so Markdown renders them literally) and preserve the URL so the reader can
# jump to the exact query in the Genie room.
_CIT_OUTER = re.compile(r"\\?\[\s*\[(\d+)\]\((https?://[^)]+)\)\s*\\?\]")
_CIT_BARE = re.compile(r"\[(\d+)\]\((https?://[^)]+)\)")
# For extracting sources back out of cleaned text + mapping to the underlying query.
_CIT_LINK = re.compile(r"\[\\\[(\d+)\\\]\]\((https?://[^)]+)\)")
_FOCUS_RE = re.compile(r"gra_focus=([0-9a-fA-F]+)")


def _clean(text: str) -> str:
    if not text:
        return ""
    text = _CIT_OUTER.sub(lambda m: f"[\\[{m.group(1)}\\]]({m.group(2)})", text)
    text = _CIT_BARE.sub(lambda m: f"[\\[{m.group(1)}\\]]({m.group(2)})", text)
    return text


def _extract_sources(text: str, id2query: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Map inline citation markers back to the queries they cite."""
    seen: dict[int, dict[str, Any]] = {}
    for m in _CIT_LINK.finditer(text or ""):
        n = int(m.group(1))
        if n in seen:
            continue
        url = m.group(2)
        fm = _FOCUS_RE.search(url)
        q = id2query.get(fm.group(1)) if fm else None
        seen[n] = {
            "n": n,
            "title": (q or {}).get("title") or f"Supporting query {n}",
            "sql": (q or {}).get("sql"),
            "url": url,
        }
    return [seen[k] for k in sorted(seen)]


def _report_blocks(response: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for item in response.get("output", []) or []:
        if item.get("type") != "message" or item.get("role") != "assistant":
            continue
        for c in item.get("content", []) or []:
            if c.get("type") != "output_text":
                continue
            meta = c.get("metadata") or {}
            cols_meta = meta.get("columns")
            if cols_meta:
                cols = [col.get("name", "") for col in cols_meta]
                rows: list[dict[str, Any]] = []
                for pr in meta.get("preview_rows", []) or []:
                    rows.append({cols[i]: pr[i] for i in range(min(len(cols), len(pr)))})
                blocks.append(
                    {
                        "kind": "table",
                        "columns": cols,
                        "rows": rows,
                        "sql": meta.get("sql"),
                        "total_row_count": meta.get("total_row_count"),
                    }
                )
            else:
                blocks.append({"kind": "text", "text": _clean(c.get("text", ""))})
    return blocks


def run(
    ws: WorkspaceClient,
    agent_id: str,
    question: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Run Agent mode to completion (server-side) and return the narrative report.

    Consumes the SSE stream and collapses it into a single result the caller can
    return synchronously:

        {"content": str, "blocks": list, "sources": list, "steps": int,
         "conversation_id": str|None, "error": str|None}

    ``content`` is the concatenation of the report's text blocks (for audit + fallback);
    ``blocks`` is the full ordered report (text + table) so the client can render the
    narrative as Markdown and any supporting data as a chart/table; ``sources`` maps the
    inline citation markers to the queries they cite. ``error`` is set if Agent mode was
    unavailable.
    """
    blocks: list[dict[str, Any]] = []
    text_parts: list[str] = []
    id2query: dict[str, dict[str, Any]] = {}
    steps = 0
    cid = conversation_id
    error: str | None = None

    for evt in stream(ws, agent_id, question, conversation_id):
        etype = evt.get("type")
        if etype == "created":
            cid = evt.get("conversation_id") or cid
        elif etype == "reasoning":
            steps += 1
        elif etype == "query":
            steps += 1
            if evt.get("id"):
                id2query[evt["id"]] = {"title": evt.get("title"), "sql": evt.get("sql")}
        elif etype == "report":
            blocks = evt.get("blocks", []) or []
            for b in blocks:
                if b.get("kind") == "text" and b.get("text"):
                    text_parts.append(b["text"].strip())
        elif etype == "error":
            error = evt.get("message") or "Agent mode failed."

    content = "\n\n".join(p for p in text_parts if p).strip()
    return {
        "content": content,
        "blocks": blocks,
        "sources": _extract_sources(content, id2query),
        "steps": steps,
        "conversation_id": cid,
        "error": error,
    }


def stream(
    ws: WorkspaceClient,
    agent_id: str,
    question: str,
    conversation_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield simplified Agent mode events as the upstream SSE stream arrives."""
    host = ws.config.host
    headers = dict(ws.config.authenticate() or {})
    headers["Content-Type"] = "application/json"

    body: dict[str, Any] = {
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": question}],
            }
        ],
        "enable_viz": False,
    }
    if conversation_id:
        body["conversation_id"] = conversation_id

    url = f"{host.rstrip('/')}/api/2.0/genie/agents/{agent_id}/responses"

    try:
        resp = requests.post(url, headers=headers, json=body, stream=True, timeout=(15, 600))
    except requests.RequestException as e:  # noqa: BLE001
        logger.exception("Agent mode request failed")
        yield {"type": "error", "message": f"Could not reach Agent mode: {e}"}
        return

    with resp:
        # The SSE body is UTF-8; requests otherwise guesses ISO-8859-1 for text/*
        # responses, which mangles em-dashes and other non-ASCII in the report.
        resp.encoding = "utf-8"
        if resp.status_code != 200:
            msg: str
            try:
                msg = (resp.json().get("error") or {}).get("message") or resp.text[:300]
            except Exception:  # noqa: BLE001
                msg = f"HTTP {resp.status_code}"
            if resp.status_code == 404 and "FEATURE" in (msg or "").upper():
                msg = (
                    "Agent mode is not enabled for this workspace. A workspace admin "
                    "can turn on 'Agent Mode APIs for Genie Agents' under Previews."
                )
            yield {"type": "error", "message": msg}
            return

        for raw in resp.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data:"):
                continue
            try:
                evt = json.loads(raw[5:].strip())
            except json.JSONDecodeError:
                continue

            etype = evt.get("type")
            if etype == "response.created":
                yield {"type": "created", "conversation_id": evt.get("response", {}).get("conversation_id")}
            elif etype == "response.output_item.done":
                item = evt.get("item", {}) or {}
                itype = item.get("type")
                if itype == "reasoning":
                    txt = " ".join(
                        c.get("text", "")
                        for c in item.get("content", []) or []
                        if c.get("type") == "reasoning_text"
                    ).strip()
                    if txt:
                        yield {"type": "reasoning", "text": txt}
                elif itype == "function_call":
                    try:
                        args = json.loads(item.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    yield {
                        "type": "query",
                        "id": item.get("id") or item.get("call_id"),
                        "title": args.get("title"),
                        "sql": args.get("sql", ""),
                    }
            elif etype == "response.completed":
                yield {"type": "report", "blocks": _report_blocks(evt.get("response", {}))}
                yield {"type": "done"}
            elif etype == "response.failed":
                err = (evt.get("response", {}).get("error") or {}).get("message") or "Agent mode failed."
                yield {"type": "error", "message": err}
