"""Create/update the Model Serving endpoint for the Member Early-Warning model.

Points ``fhlb-member-credit-risk`` at the latest Unity Catalog version of
``fhlb.des_moines.member_early_warning`` (CPU, scale-to-zero for the demo).

    uv run --with mlflow --with databricks-sdk python ml/deploy_serving.py
"""
from __future__ import annotations

import time

import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    EndpointStateConfigUpdate,
    EndpointStateReady,
    ServedEntityInput,
)
from mlflow.tracking import MlflowClient

MODEL_NAME = "fhlb.des_moines.member_early_warning"
ENDPOINT_NAME = "fhlb-member-credit-risk"


def latest_version() -> str:
    mlflow.set_registry_uri("databricks-uc")
    client = MlflowClient(registry_uri="databricks-uc")
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    if not versions:
        raise RuntimeError(f"No versions registered for {MODEL_NAME}")
    return str(max(int(v.version) for v in versions))


def main() -> None:
    ws = WorkspaceClient()
    version = latest_version()
    print(f"Deploying {MODEL_NAME} v{version} -> {ENDPOINT_NAME}")

    served = ServedEntityInput(
        entity_name=MODEL_NAME,
        entity_version=version,
        workload_size="Small",
        scale_to_zero_enabled=True,
    )
    config = EndpointCoreConfigInput(name=ENDPOINT_NAME, served_entities=[served])

    existing = {e.name for e in ws.serving_endpoints.list()}
    if ENDPOINT_NAME in existing:
        print("Endpoint exists; updating config...")
        ws.serving_endpoints.update_config(
            name=ENDPOINT_NAME, served_entities=[served]
        )
    else:
        print("Creating endpoint...")
        ws.serving_endpoints.create(name=ENDPOINT_NAME, config=config)

    print("Waiting for endpoint to become READY (this can take 10-20 min)...")
    deadline = time.time() + 30 * 60
    while time.time() < deadline:
        ep = ws.serving_endpoints.get(ENDPOINT_NAME)
        state = ep.state
        ready = getattr(state, "ready", None)
        update = getattr(state, "config_update", None)
        print(f"  ready={ready} config_update={update}")
        if ready == EndpointStateReady.READY:
            print(f"Endpoint {ENDPOINT_NAME} is READY.")
            return
        if update == EndpointStateConfigUpdate.UPDATE_FAILED:
            raise RuntimeError("Config update failed; check the serving UI logs.")
        time.sleep(20)
    raise TimeoutError("Endpoint did not become READY within 30 min.")


if __name__ == "__main__":
    main()
