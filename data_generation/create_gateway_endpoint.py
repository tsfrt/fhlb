"""
Create the fhlb-governed-llm serving endpoint: an AI Gateway-governed wrapper around
the Databricks Claude Sonnet foundation model. Adds PII guardrails, rate limits,
usage tracking, and an inference table in fhlb.governance. This is the single
governed LLM the app routes ALL narratives + the Affordable Housing Assistant through.
"""
import json
import os
import subprocess

PROFILE = os.environ.get("FHLB_PROFILE", "fevm-serverless-stable-blj52t")
DBX = "/opt/homebrew/bin/databricks"
HOST = os.environ.get("FHLB_HOST", "https://fevm-serverless-stable-blj52t.cloud.databricks.com")
ENV = {**os.environ, "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
       "DATABRICKS_CLI_DO_NOT_EXECUTE_NEWER_VERSION": "1"}

ENDPOINT = "fhlb-governed-llm"
BASE_MODEL = "databricks-claude-sonnet-4-6"


def api(method, path, body=None):
    args = [DBX, "api", method, path, "--profile", PROFILE]
    if body is not None:
        args += ["--json", json.dumps(body)]
    out = subprocess.run(args, capture_output=True, text=True, env=ENV)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"_err": (out.stderr or out.stdout)[:600]}


config = {
    "name": ENDPOINT,
    "config": {
        "served_entities": [
            {
                "name": "governed-claude",
                "external_model": {
                    "name": BASE_MODEL,
                    "provider": "databricks-model-serving",
                    "task": "llm/v1/chat",
                    "databricks_model_serving_config": {
                        "databricks_workspace_url": HOST,
                        "databricks_api_token": "{{secrets/fhlb/gateway_token}}",
                    },
                },
            }
        ]
    },
    "ai_gateway": {
        "guardrails": {
            "input": {
                "pii": {"behavior": "MASK"},
                "invalid_keywords": ["ssn", "social security number"],
            },
            "output": {"pii": {"behavior": "MASK"}},
        },
        "rate_limits": [{"calls": 200, "renewal_period": "minute", "key": "endpoint"}],
        "usage_tracking_config": {"enabled": True},
        "inference_table_config": {
            "enabled": True,
            "catalog_name": "fhlb",
            "schema_name": "governance",
            "table_name_prefix": "fhlb_llm",
        },
    },
}

existing = api("get", f"/api/2.0/serving-endpoints/{ENDPOINT}")
if existing.get("name") == ENDPOINT:
    print(f"Endpoint {ENDPOINT} already exists; updating AI Gateway config...")
    r = api("put", f"/api/2.0/serving-endpoints/{ENDPOINT}/ai-gateway", config["ai_gateway"])
    print(json.dumps(r, indent=2)[:1200])
else:
    print(f"Creating endpoint {ENDPOINT}...")
    r = api("post", "/api/2.0/serving-endpoints", config)
    print(json.dumps(r, indent=2)[:1500])
