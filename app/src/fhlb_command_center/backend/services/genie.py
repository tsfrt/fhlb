"""Genie natural-language Q&A via the SDK Conversation API."""
from __future__ import annotations

from typing import Any

from databricks.sdk import WorkspaceClient

from .lakehouse import _cast


def ask(
    ws: WorkspaceClient,
    space_id: str,
    question: str,
    conversation_id: str | None = None,
    enable_visualization: bool = True,
) -> dict[str, Any]:
    """Ask a Genie space a question; return answer text, generated SQL, and rows.

    When ``conversation_id`` is supplied the question continues that conversation so
    Genie keeps prior context (a real multi-turn chat); otherwise a new one starts.

    With ``enable_visualization`` (Beta) Genie may also attach a rendered chart; we
    surface its identifiers so the client can fetch the PNG via the viz proxy.
    """
    if conversation_id:
        msg = ws.genie.create_message_and_wait(
            space_id, conversation_id, question, enable_visualization=enable_visualization
        )
    else:
        msg = ws.genie.start_conversation_and_wait(
            space_id, question, enable_visualization=enable_visualization
        )

    answer: str | None = None
    sql: str | None = None
    viz: dict[str, Any] | None = None
    query_attachment_id: str | None = None
    for att in msg.attachments or []:
        if att.text and att.text.content:
            answer = att.text.content
        if att.query and att.query.query:
            sql = att.query.query
            query_attachment_id = att.attachment_id
            if not answer and att.query.description:
                answer = att.query.description
        if att.viz and att.attachment_id:
            viz = {"title": att.viz.title, "attachment_id": att.attachment_id}

    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    if query_attachment_id and msg.conversation_id and msg.id:
        try:
            # Fetch per-attachment: with visualization enabled the message-level
            # result comes back empty, but the query attachment carries the rows.
            res = ws.genie.get_message_attachment_query_result(
                space_id, msg.conversation_id, msg.id, query_attachment_id
            )
            sr = res.statement_response
            if sr and sr.manifest and sr.manifest.schema and sr.result:
                cols = sr.manifest.schema.columns or []
                columns = [c.name or "" for c in cols]
                types = [c.type_name.value if c.type_name else None for c in cols]
                for raw in sr.result.data_array or []:
                    rows.append({columns[i]: _cast(raw[i], types[i]) for i in range(len(columns))})
        except Exception:  # noqa: BLE001 - query result is best-effort for the demo
            pass

    if viz is not None:
        viz["message_id"] = msg.id

    return {
        "answer": answer or "Genie did not return a text answer.",
        "sql": sql,
        "columns": columns,
        "rows": rows[:200],
        "conversation_id": msg.conversation_id,
        "message_id": msg.id,
        "viz": viz,
    }


def download_viz(
    ws: WorkspaceClient,
    space_id: str,
    conversation_id: str,
    message_id: str,
    attachment_id: str,
) -> bytes:
    """Download the rendered PNG for a Genie visualization attachment (Beta)."""
    name = (
        f"spaces/{space_id}/conversations/{conversation_id}"
        f"/messages/{message_id}/attachments/{attachment_id}"
    )
    resp = ws.genie.download_message_attachment_visualization(name=name)
    return resp.contents.read() if resp.contents else b""
