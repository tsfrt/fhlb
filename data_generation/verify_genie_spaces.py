"""
Verify each FHLB Genie space answers a representative question from the demo doc.
Starts one conversation per space, polls to completion, prints the generated SQL
and the row count / answer snippet.
"""
import json
import os
import subprocess
import time

PROFILE = "fevm-serverless-stable-blj52t"
DBX = "/opt/homebrew/bin/databricks"
ENV = {**os.environ, "PATH": "/opt/homebrew/bin:/usr/bin:/bin", "DATABRICKS_CLI_DO_NOT_EXECUTE_NEWER_VERSION": "1"}

SPACES = [
    ("Credit & Collateral (CRO)", "01f19fca2c3f12fdb24b4c62cd498636",
     "Which pledged collateral types had the highest exception rates in the most recent collateral reviews?"),
    ("Finance & Treasury (CFO)", "01f19fca2c7b192593a458a089f2170a",
     "What is the unrealized gain or loss on the agency MBS portfolio by vintage year and duration bucket?"),
    ("Member & Products (CBO)", "01f19fca2ca91bd18bdd24fa575ee36e",
     "Which members are originating mortgages but not delivering into the MPF Program, and what outlet are they using instead? Limit 5."),
    ("Mission & AHP", "01f19fca2cd810c68e2c9008491dfd8d",
     "What is year-to-date progress against the $200 million housing affordability pledge, by program?"),
    ("Data Governance & Operations (CIO)", "01f19fca2d0618bfa933efd57156faed",
     "Which reports due to the FHFA this quarter have open data quality exceptions, and which SQL Server instances do they trace back to?"),
]


def api(method, path, body=None):
    args = [DBX, "api", method, path, "--profile", PROFILE]
    if body is not None:
        args += ["--json", json.dumps(body)]
    out = subprocess.run(args, capture_output=True, text=True, env=ENV)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"_err": (out.stderr or out.stdout)[:300]}


def run(space_id, question):
    start = api("post", f"/api/2.0/genie/spaces/{space_id}/start-conversation", {"content": question})
    cid, mid = start.get("conversation_id"), start.get("message_id")
    if not cid:
        return {"error": start.get("_err", start)}
    for _ in range(30):
        msg = api("get", f"/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}")
        st = msg.get("status")
        if st in ("COMPLETED", "FAILED"):
            return msg
        time.sleep(6)
    return {"error": "timeout"}


for name, sid, q in SPACES:
    print(f"\n{'='*70}\n{name}\nQ: {q}")
    msg = run(sid, q)
    if msg.get("error"):
        print(f"  ERROR: {msg['error']}")
        continue
    sql = ans = None
    for a in msg.get("attachments", []) or []:
        if a.get("query"):
            sql = a["query"].get("query", "")
        if a.get("text"):
            ans = a["text"].get("content", "")
    qr = msg.get("query_result") or {}
    rc = qr.get("row_count")
    if sql:
        print("  SQL (first 500 chars):")
        print("   " + sql[:500].replace("\n", "\n   "))
    if rc is not None:
        print(f"  rows returned: {rc}")
    if ans:
        print("  ANSWER:", ans[:400].replace("\n", " "))
    print(f"  STATUS: {msg.get('status')}")
