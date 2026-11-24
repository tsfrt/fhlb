# Building a Databricks App Like This with Cursor

A practical, opinionated guide to building a full-stack, data-and-AI-native
Databricks App — like the **FHLB Des Moines Executive Command Center** in this
repo — using Cursor as the primary development environment.

It is written two ways at once:

- **What** the ideal architecture looks like (so the output is correct), and
- **How** to drive Cursor (agent, Plan mode, rules, skills, subagents, MCP) so
  you get there quickly and repeatably.

---

## 1. What we're building

The target is a single product made of several cooperating Databricks surfaces,
all living in one Git monorepo and all deployed as **Databricks Asset Bundles
(DABs)**:

| Layer | Technology | In this repo |
|---|---|---|
| Synthetic/seed data | PySpark + Faker | `data_generation/` |
| Curated lakehouse | Lakeflow Spark Declarative Pipeline (medallion) | `pipeline/` |
| App OLTP state | Lakebase (managed Postgres) + Prisma migrations | `db/` |
| Classical ML | XGBoost PD model + MLflow + Model Serving | `ml/` |
| Governed LLM | AI Gateway endpoint (guardrails) | `data_generation/create_gateway_endpoint.py` |
| Natural-language BI | Genie spaces (per persona) | `data_generation/create_genie_spaces.py` |
| The app itself | React + FastAPI via **apx**, deployed as a Databricks App | `app/` |
| Cost/ops telemetry | AI/BI (Lakeview) dashboard over `system.billing` | `dashboards/` |

The guiding principle: **every component is code, every component is a bundle,
and every component is reproducible in a fresh workspace from `git clone`.**

---

## 2. One-time setup for Cursor

Before writing a line of app code, get Cursor itself configured. This is what
makes the agent productive instead of generic.

### 2.1 Rules (persistent guidance)

Encode the non-negotiables as **Cursor Rules** so every agent turn respects
them. The rules that shaped this project:

- All applications target the Databricks platform; build as **Asset Bundles**
  with a Databricks **`app.yaml`**.
- Each project ships **GitHub Actions** that manage Databricks deployment:
  - feature branches → deploy a **preview app**,
  - tags on `main` → release a new **production** version,
  - only an **approved PR** may merge to `main`.
- Feature PRs use **Lakebase branching** (a dedicated branch forked from the
  production database), and **Prisma** manages migrations on the production
  branch.

Put these in a rule file (see the `create-rule` skill) so they are applied
automatically rather than re-explained in every prompt.

### 2.2 Skills, subagents, and MCP

- **Skills** give the agent domain playbooks. The Databricks-oriented ones used
  here include `databricks-app-apx`, `databricks-bundles`, `databricks-lakebase`,
  `databricks-model-serving`, `databricks-genie`, `databricks-aibi-dashboards`,
  `databricks-unity-catalog`, and `databricks-config`. When a task matches a
  skill, read it **first** and follow it.
- **Subagents** parallelize specialized work: `databricks-apps-developer` for
  scaffolding/deploying the app, `web-devloop-tester` for the local UI inner
  loop, plus `bugbot` / `security-review` before merging.
- **MCP** (e.g. `user-databricks-mcp`) exposes the workspace directly to the
  agent. When MCP is flaky, fall back to the **Databricks CLI + Python SDK** —
  that fallback is what kept this project moving.

### 2.3 Authentication

Authenticate the CLI once per workspace with OAuth U2M and reference it by
profile everywhere:

```bash
databricks auth login --host https://<workspace>.cloud.databricks.com --profile <name>
```

Store the profile in `app/.env` (git-ignored) as
`DATABRICKS_CONFIG_PROFILE=<name>` so the SDK and bundle pick it up. **Never**
commit the `.env`.

> Lesson learned: U2M login is interactive (Okta + device MFA). It cannot be
> automated by the agent and must be completed in the browser. Budget for it.

---

## 3. The Cursor working loop

The ideal rhythm for a build of this size:

1. **Plan mode first.** For anything multi-step, switch to Plan mode and let the
   agent produce a plan + todo list. Review it before executing. Keep the plan
   file read-only and track progress with the todo list.
2. **One todo in progress at a time.** Mark items `in_progress` → `completed`
   as you go so the thread stays legible and resumable.
3. **Prefer specialized tools over shell.** Use the file tools for reads/edits,
   `rg` for search, and skills/subagents for domain work. Reserve the terminal
   for real system commands (git, `databricks`, `apx`, `uv`).
4. **Verify every layer where it lives.** Don't assume. Smoke-test SQL via the
   Statement Execution API, hit serving endpoints directly, run the app against
   the local `apx dev` server, and check `system.billing` for cost.
5. **Commit in small, reviewable slices** and open PRs; let Bugbot/Security
   review before merge.

---

## 4. Monorepo layout

Keep each deployable concern in its own top-level directory, each with its own
bundle where appropriate:

```
.
├── app/                  # Databricks App (apx: React + FastAPI) + databricks.yml + app.yml
│   └── src/<app_slug>/
│       ├── backend/      # FastAPI: core/_config.py, services/, router.py
│       └── ui/           # React: routes/, components/{shell,common,ui}, styles/
├── pipeline/             # Lakeflow SDP bundle: resources/*.pipeline.yml + src/transformations/
├── db/                   # Lakebase: prisma/schema.prisma + migrations + apply scripts
├── ml/                   # train.py, deploy_serving.py, validate_model.py, early_warning_model.py
├── data_generation/      # seed data + create_gateway_endpoint.py + create_genie_spaces.py + lakebase_setup.py
├── dashboards/           # *.lvdash.json (serialized Lakeview dashboards)
└── docs/                 # this guide, demo scripts, etc.
```

Why this shape works well with Cursor: each directory is a self-contained
context the agent can reason about, and each maps cleanly to one provisioning
step and (ideally) one CI job.

---

## 5. Build sequence (data up, UI last)

Build bottom-up so every layer has something real to sit on. Each step is a
discrete, verifiable unit of work — ideal for a single Cursor todo.

### Step 1 — Data foundation (`data_generation/`, `pipeline/`)
- Generate realistic seed data (PySpark + Faker) into Unity Catalog
  (`catalog=fhlb`, `schema=des_moines` here).
- Model the curated layer as a **Lakeflow Spark Declarative Pipeline** using the
  medallion pattern (bronze → silver → gold). Transformations are plain Python
  modules in `pipeline/src/transformations/`, wired by a
  `resources/*.pipeline.yml` in the bundle.
- **Verify:** query a gold table via the Statement Execution API.

### Step 2 — App OLTP state (`db/`)
- Provision a **Lakebase** (managed Postgres) instance for app state
  (annotations, watchlists, audit — things that don't belong in the lakehouse).
- Define the schema in `prisma/schema.prisma`; manage changes with **Prisma
  migrations** on the production branch.
- For feature work, use **Lakebase branching**: fork a feature branch from
  production so schema experiments are isolated.
- **Verify:** `prisma migrate status` + a round-trip insert/select.

### Step 3 — Classical ML (`ml/`)
- Keep the **feature contract** in one place (`early_warning_model.py`) so
  training (`train.py`) and serving agree. Train against the gold tables, log to
  **MLflow**, and register to the Unity Catalog model registry.
- Deploy with `deploy_serving.py` to a **Model Serving** endpoint
  (`fhlb-member-credit-risk`).
- **Validate independently** (`validate_model.py`): build a stratified holdout,
  score through the *deployed* endpoint, and compute ROC-AUC/PR-AUC/KS/Brier +
  train–serve parity. This catches drift between training and serving.

### Step 4 — Governed LLM + Genie
- Create an **AI Gateway** serving endpoint (`fhlb-governed-llm`) with
  guardrails/rate limits so all narrative generation is governed and auditable
  (`create_gateway_endpoint.py`).
- Create **Genie spaces** scoped per persona for natural-language BI
  (`create_genie_spaces.py`). Record the space ids in app config.
- **Verify:** one governed completion and one Genie query end to end.

### Step 5 — The app (`app/`)
- Scaffold with **apx** (`databricks-app-apx` skill / `databricks-apps-developer`
  subagent): FastAPI backend + React/shadcn frontend with an auto-generated
  TypeScript client from the OpenAPI schema.
- Centralize everything environment-specific in **one config object**
  (`backend/core/_config.py`): warehouse id, catalog/schema, endpoint names,
  Lakebase instance/db, Genie space ids. Read it from env with a project prefix.
- Bind resources (not hardcoded ids) in `databricks.yml` and inject them via
  `app.yml` `valueFrom`:

  ```yaml
  # app.yml — resources are injected as env vars, not baked in
  env:
    - name: FHLB_COMMAND_CENTER_WAREHOUSE_ID
      valueFrom: sql-warehouse
    - name: FHLB_COMMAND_CENTER_GATEWAY_ENDPOINT
      valueFrom: serving-endpoint
  ```

- **Inner loop:** `apx dev start` → iterate → `apx dev check` (type-check + lint)
  → verify in the browser via the `web-devloop-tester` subagent.

> Lesson learned: the deployed app sits behind Okta SSO, which a headless
> browser can't pass. Do UI verification against the **local `apx dev`** server,
> and smoke-test backend behavior via the SDK/endpoints directly.

### Step 6 — Cost & ops telemetry (`dashboards/`)
- Build an **AI/BI (Lakeview)** dashboard over `system.billing.usage` joined to
  `system.billing.list_prices`, scoped to *this* app's components via
  `usage_metadata` (`app_name`, `endpoint_name`, `dlt_pipeline_id`,
  `warehouse_id`, and `project_id` = the Lakebase instance uid).
- Serialize it to `*.lvdash.json` and commit it so the dashboard is code too.
- **Always test the SQL** before publishing — every tile query should run green.

> Lesson learned: Lakebase cost shows up under `usage_metadata.project_id`
> (the instance uid), **not** `database_instance_id` (which is NULL). Attribution
> filters have to be component-aware.

---

## 6. Deployment & CI/CD

### 6.1 Bundles and targets
Everything deploys with Asset Bundles:

```bash
databricks bundle deploy -p <profile>
databricks bundle run <resource> -p <profile>
```

Use **bundle variables** for anything workspace-specific (warehouse id, endpoint
names, Lakebase instance) and define a **target per workspace**:

```yaml
targets:
  dev:
    mode: development
    default: true
  prod:
    mode: production
    workspace:
      host: https://<prod-workspace>.cloud.databricks.com
    variables:
      warehouse_id: "<prod-warehouse-id>"
```

> This is exactly what makes "redeploy to a new workspace" tractable: add a
> target with the new host + resource ids, re-provision the dependency stack
> (warehouse binding, serving endpoints, Lakebase, Genie spaces), then deploy.

### 6.2 GitHub Actions (per project)
Wire the deployment policy from your rules into Actions:

- **Feature branch push** → `bundle deploy` to a **preview** target (a disposable
  preview app) + create a **Lakebase feature branch** from production.
- **PR merge to `main`** → requires an **approved PR** (branch protection); no
  direct pushes.
- **Tag on `main`** (e.g. `v1.2.0`) → `bundle deploy` to the **production**
  target and release the new app version; run **Prisma migrations** against the
  production Lakebase branch.

Use OAuth (service principal) secrets for the Actions runner, and gate prod with
a GitHub **Environment** approval.

---

## 7. Quality gates before merge

- `apx dev check` (Python + TypeScript type-check and lint) must be clean.
- Run `validate_model.py` when touching features/training/serving.
- Run the **Bugbot** subagent on branch changes, and the **Security Review**
  subagent when changes touch auth, data access, or secrets.
- Keep a tight `.gitignore`: no `__pycache__`, `.venv`, `node_modules`,
  `.build`, generated `_version.py`/`_metadata.py`, `ml/artifacts/*`, `.env`, or
  review scratch dirs.

---

## 8. Hard-won lessons (the short list)

1. **Resources are workspace-specific; config is one object.** Centralize ids
   and names so moving workspaces is a config/target change, not a code hunt.
2. **A fresh workspace needs the whole stack re-provisioned** — catalog data is
   not enough. Warehouse, serving endpoints, Lakebase, and Genie spaces all have
   to exist before the app's bundle can bind to them.
3. **Interactive auth is a human step.** U2M SSO/MFA can't be scripted by the
   agent; plan the handoff.
4. **Verify in the layer that owns the truth** — SQL via Statement Execution,
   models via the serving endpoint, UI via local `apx dev`, cost via
   `system.billing`.
5. **Everything is code**: pipelines, migrations, model deploy, gateway, Genie,
   dashboards, and the app. If it isn't in the repo, it isn't reproducible.

---

*Grounded in the FHLB Des Moines Executive Command Center build. Use it as a
template: swap the domain, keep the shape.*
