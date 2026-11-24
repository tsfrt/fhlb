# Getting Better at the Coding Harness: A Cursor Playbook

How to drive Cursor (or any agent harness) from idea to shipped app, using the
FHLB Executive Command Center as the running example.

This is the companion to [`building-databricks-apps-with-cursor.md`](./building-databricks-apps-with-cursor.md).
That doc covers **what to build** (architecture and build order). This one
covers **how to work with the agent** so the build goes faster and breaks less.

---

## 1. The mental model

A harness is four things wrapped around a model:

```
        ┌────────────────────────────────────────────┐
        │  CONTEXT   what the agent knows right now  │  rules, AGENTS.md, skills,
        │                                            │  @files, specs, chat history
        ├────────────────────────────────────────────┤
        │  TOOLS     what the agent can do           │  file edit, shell, MCP,
        │                                            │  subagents, browser
        ├────────────────────────────────────────────┤
        │  LOOP      how it checks its own work      │  tests, type-check, lint,
        │                                            │  smoke tests, screenshots
        ├────────────────────────────────────────────┤
        │  YOU       intent, taste, and decisions    │  specs, plans, review, approvals
        └────────────────────────────────────────────┘
```

The model is the same for everyone. Results differ because of what the other
three layers contain. Skill at a harness comes down to four habits:

1. **Put the right context in front of the agent.** Short, specific and current.
2. **Give it a way to check itself.** An agent that can't verify will guess.
3. **Keep each task small enough to review.** You must understand what landed.
4. **Write down what you learn.** A lesson that isn't in a rule or doc gets re-learned every session.

Most of the rest of this doc is those four habits applied at each phase.

---

## 2. The lifecycle at a glance

| Phase | Your job | Agent's job | Output artifact |
|---|---|---|---|
| 1. Frame | State the outcome and audience | Interview you, challenge assumptions | One-paragraph brief |
| 2. Design | Pick the shape: personas, screens, data | Propose options and trade-offs | `docs/spec.md`, mock or demo script |
| 3. Plan | Approve scope and order | Explore the repo, draft tasks with acceptance checks | Plan + todo list |
| 4. Set up | Decide conventions | Write rules, scaffold, wire CI | `.cursor/rules`, `AGENTS.md`, CI |
| 5. Build | Steer, review diffs | Implement one vertical slice at a time | Small commits |
| 6. Verify | Define "done" | Run checks in the layer that owns the truth | Passing checks, screenshots |
| 7. Review and ship | Approve | Bugbot and security review, PR, deploy | Merged PR, tagged release |
| 8. Retro | Decide what to codify | Update rules, skills and docs | Better rules for next time |

Skipping phases 1 to 4 is the most common reason a harness feels unreliable.
The agent is fast enough that unclear intent produces a lot of wrong code quickly.

---

## 3. Phase 1: Frame the problem

Before opening a chat, write 3 to 5 sentences covering:

- **Who** uses it (for FHLB: CEO/Board, CFO, CRO, CBO, CIO, Community Investment).
- **What decision** each person makes with it.
- **What "wow" looks like** in the first 5 minutes.
- **Hard constraints** (Databricks only, governed AI, bundles, Lakebase for state).

Then let the agent interview you instead of guessing. This prompt works well:

> I want to build [one paragraph]. Before proposing anything, ask me the 5 to 8
> questions that would most change the design. Use the AskQuestion tool with
> options where you can. Don't write code yet.

Why it works: the agent's defaults are generic. The interview forces your real
constraints into the context before they get baked into the code.

---

## 4. Phase 2: Design

### 4.1 Work backwards from the demo

The best spec in this repo is `DEMO_SCRIPT.md`. It states, per persona, what
the audience sees, what you say, and the business impact. Writing it first
(even as rough bullets) gives the agent:

- a concrete **screen inventory** (KPI band, anomaly radar, SOFR slider...),
- the **data each screen needs**, so the schema follows from it,
- a built-in **acceptance test**: "can I deliver this walkthrough?"

Rule of thumb: **if you can't script the demo, you can't specify the app.**

### 4.2 Write a spec the agent can use

Keep `docs/spec.md` short and structured. For each persona or screen:

```markdown
## CRO: Credit & Collateral
Goal: find where credit risk is concentrating before the rating cadence does.
Panels:
  - Member Early-Warning: ranked PD, rating-gap flag, top drivers
  - Watchlist: persisted in Lakebase
Data: fhlb.des_moines.members, advances, collateral; serving endpoint X
Done when: rescore calls the live endpoint; watchlist survives refresh
Out of scope: write-back to core banking
```

Always include **Done when** and **Out of scope**. Those two lines prevent most
rework and scope creep.

### 4.3 Design the contracts before the code

Decide these early and write them down. They are expensive to change later:

1. **Data model**: tables, grain, keys (`members` as the spine).
2. **API contract**: FastAPI routes and Pydantic models. With apx, the OpenAPI
   schema generates the TypeScript client, so the backend contract *is* the
   frontend contract. Change the model, regenerate, and the compiler tells you
   what broke.
3. **Feature contract** for ML: one module shared by training and serving.
4. **Config surface**: one config object, resources bound in `databricks.yml`.

### 4.4 Design the UI with visuals, not prose

For UI, describe layout by reference rather than adjectives:

- Paste a screenshot or sketch and say "match this layout".
- Name a component library (shadcn/ui) so the agent doesn't invent primitives.
- Build one **reference screen** (the Executive Overview) and then say "make the
  CFO screen follow the same shell, spacing, and components". Consistency comes
  from precedent, not from instructions.

---

## 5. Phase 3: Plan

### 5.1 Use Plan mode for anything over ~3 steps

Switch to Plan mode, then ask for a plan. The agent explores the codebase
read-only and proposes an approach. You review it **before** any file changes.
Reviewing a plan costs minutes. Reviewing a wrong implementation costs hours.

### 5.2 What a good plan contains

- **Ordered tasks**, each small enough for one commit.
- **A verification step per task**, for example "run the query against the
  warehouse", "hit the endpoint", "`apx dev check` clean".
- **Dependencies called out** (the warehouse and serving endpoint must exist
  before the app's bundle can bind to them).
- **Open questions** for you, not silent assumptions.
- **Risks**, such as interactive auth or workspace-specific ids.

### 5.3 Plan prompt template

```
Goal: <outcome in one sentence>
Context: @docs/spec.md @app/databricks.yml
Constraints: <rules that matter, or "see .cursor/rules">
Deliver a plan with: ordered tasks, a verification step for each,
dependencies, risks, and questions for me. Do not edit files.
```

### 5.4 Review the plan like a code review

Ask yourself:

- Is the order bottom-up (data, then state, then ML, then API, then UI)?
- Does each task have a check that would **fail** if the task were wrong?
- Is anything large enough to split further?
- Did it quietly choose something I would have decided differently?

Push back in the same chat. Editing a plan is nearly free.

### 5.5 Use the todo list as shared state

Keep one task `in_progress` at a time. It keeps the thread legible and lets you
resume in a new chat ("continue from todo 4").

---

## 6. Phase 4: Set up the harness itself

This phase has the highest leverage and is the one most often skipped.

### 6.1 Rules: what the agent must always know

Rules are persistent instructions applied automatically. Keep them **short,
specific, and testable**. Good rules state facts the agent can't infer:

```markdown
# .cursor/rules/databricks.mdc  (alwaysApply: true)
- Every deployable is a Databricks Asset Bundle with an app.yaml.
- Never hardcode ids. Resources are bound in databricks.yml and injected via
  app.yml valueFrom. Config is read in backend/core/_config.py only.
- Feature branches deploy a preview app and a Lakebase branch from production.
- Prisma owns migrations on the production Lakebase branch. Never hand-edit prod.
- Verify in the layer that owns the truth (see AGENTS.md "Verification").
```

Bad rules are vague ("write clean code") or huge. A 500-line rule file gets
skimmed by the model just like it would by a person.

Use the `create-rule` skill to author them. Scope rules with globs
(`app/src/**/ui/**` gets the React conventions) so they load only when relevant.

### 6.2 `AGENTS.md`: the project README for the agent

A short file at the repo root with:

- **Layout**: which directory does what (the monorepo map).
- **Commands**: how to run, check, test, and deploy each piece.
- **Verification**: how to prove each layer works.
- **Gotchas**: things that cost you time once.

Example gotchas from this project that belong here:

- U2M login is interactive. The agent can't complete it. Stop and ask.
- Lakebase cost is under `usage_metadata.project_id`, not `database_instance_id`.
- The deployed app is behind Okta. Test the UI locally with `apx dev`.
- A fresh workspace needs the whole stack re-provisioned, not just data.

Every gotcha you write down is a mistake the agent won't repeat.

### 6.3 Skills: playbooks loaded on demand

Skills hold deep, task-specific procedure (for example `databricks-bundles`,
`databricks-lakebase-autoscale`, `databricks-model-serving`, `databricks-genie`,
`databricks-app-apx`). Use them when the task matches. A skill carries knowledge
you shouldn't have to re-explain: API shapes, CLI flags, known failure modes.

Tip: name the skill in your prompt ("use the databricks-bundles skill") when the
agent hasn't picked it up on its own.

### 6.4 MCP and CLI: reach into the real system

MCP servers (like the Databricks one) give the agent direct access to the
workspace. When they're flaky, the CLI and SDK are a reliable fallback. Teach
the agent both in `AGENTS.md` so it can switch without asking.

### 6.5 Codify your policies as CI early

Your policies (preview app per feature branch, tagged release to prod, only
approved PRs merge to `main`) should be **GitHub Actions and branch protection**,
not memory. Set these up in Phase 4, before building features, so every later
PR flows through them.

### 6.6 Repo hygiene is context hygiene

A clean repo gives the agent less noise to wade through. Keep `.gitignore`
tight (`__pycache__`, `node_modules`, `.build`, `.env`, generated files, review
screenshots). Large generated directories also slow indexing and search.

---

## 7. Phase 5: Build

### 7.1 Build in vertical slices, not horizontal layers

Don't ask for "all the backend" and then "all the frontend". Ask for one thin
slice that works end to end:

> Slice 1: the KPI band on the Executive Overview. One SQL query, one FastAPI
> route, one React component, rendered against real data.

You find integration problems on slice 1, while they're cheap. Later slices
copy the pattern the first one established.

### 7.2 Anatomy of a good build prompt

```
Task:        what to build, in one sentence
Context:     @files the agent should read first (existing pattern to follow)
Constraints: what not to touch, which conventions apply
Done when:   the observable check that proves it works
```

Example:

> Add the "Ratings past cadence" table to the CRO screen.
> Follow the pattern in @routes/cro.tsx and @services/credit.py.
> Don't change the shared shell.
> Done when: `apx dev check` is clean and the table renders live rows locally.

Point at an **existing example** whenever one exists. "Do it like X" beats a
paragraph of style rules.

### 7.3 Keep context lean

Context is finite, and long chats degrade. Practical rules:

- **One chat per task or slice.** Start fresh when the goal changes.
- Attach files with `@` rather than pasting them. Reference code, don't retype it.
- If the agent starts repeating itself, forgetting decisions, or contradicting
  earlier work, the context is stale. Summarize the state in a few lines and
  start a new chat.
- Put durable decisions in the repo (spec, rules), not only in chat. Chat is
  disposable. Files are not.

### 7.4 Use subagents for parallel, isolated work

Subagents are for work that is independent or noisy:

- **explore**: broad codebase search without bloating your main context.
- **databricks-apps-developer**: scaffolding and deploying Databricks Apps.
- **web-devloop-tester**: run the dev server, drive the browser, check console.
- **bugbot** and **security-review**: independent review before merge.
- **best-of-n-runner**: try a risky approach in an isolated worktree.

Run independent subagents in parallel. For example, while the UI slice builds,
another agent can write the serving-endpoint validation script. Don't use a
subagent for a 2-line change. The overhead isn't worth it.

### 7.5 Keep humans in the loop at the right points

Review every diff at the **contract boundaries**: schema, API models, config,
migrations, auth, CI, bundle resources. Skim the internals of a component that
the type-checker and a screenshot have already vetted.

### 7.6 Commit small and often

One slice, one commit (or PR). Small commits give you:

- cheap rollback when the agent goes off the rails,
- a readable history,
- reviewable PRs for Bugbot.

Commit **before** a risky refactor so you have a clean checkpoint.

---

## 8. Phase 6: Verify (the most important loop)

An agent without feedback guesses. An agent with feedback converges. Give it
the cheapest check that would fail if the work were wrong, **in the layer that
owns the truth**:

| Layer | The check | Don't rely on |
|---|---|---|
| SQL / pipeline | Run the query against the warehouse via Statement Execution; assert row counts and sample values | "The SQL looks right" |
| Lakebase / Prisma | `prisma migrate status` and a round-trip insert/select | Reading the migration file |
| ML model | `validate_model.py` through the **deployed endpoint**; train-serve parity | Notebook metrics only |
| Gateway / Genie | One real governed call and one real Genie query | Config looks fine |
| Backend | Call the route locally and check the response shape | Type-check alone |
| Frontend | `apx dev check`, then a local browser run with a screenshot | The deployed app (behind Okta) |
| Cost | Query `system.billing.usage` | An estimate |
| Whole app | Walk the demo script | "It builds" |

Practices that raise reliability:

- **Make the check part of the task.** "Done when X passes", not "implement X".
- **Ask for evidence.** "Show me the query output / the screenshot", not "it works".
- **Test the failure path** too: empty data, endpoint down, off-topic question
  to the governed assistant (it should decline).
- **Add tests where logic is non-trivial.** This repo currently has none;
  see section 12. Start with the pure logic (SOFR sensitivity math, rating-gap
  flag, anomaly ranking), since these are cheap to test and costly to get wrong.
- **Use screenshots as a feedback channel.** The `.ew-review` and
  `.header-review` folders are this pattern: screenshot, critique, adjust.
  Keep it, but write the images outside the repo or git-ignore them.

---

## 9. Debugging with an agent

When something breaks:

1. **Give it the evidence**: the exact error, relevant logs (`apx dev logs`),
   the command you ran. Don't paraphrase.
2. **Ask for hypotheses before fixes.** "List the 3 most likely causes and the
   cheapest check for each." Then run the checks.
3. **Change one thing at a time**, and re-run the same check.
4. **Two failed attempts means stop.** If the agent has tried the same class of
   fix twice, the premise is wrong. Reset: restate the problem, add new
   evidence, or start a fresh chat. Don't let it thrash.
5. **Know the human-only steps.** Interactive OAuth/MFA, approvals, and UI
   consent screens can't be automated. When the agent hits one, it should stop
   and tell you, not loop.
6. **Capture the root cause** in `AGENTS.md` once found.

---

## 10. Phase 7: Review and ship

Before merging:

1. **You read the diff.** Especially contracts and config.
2. **Bugbot** on branch changes, for logic bugs and regressions.
3. **Security review** when the change touches auth, data access, secrets, or
   user input (the governed assistant and any SQL built from input).
4. **CI green**: type-check, lint, tests, bundle validate.
5. **Preview app** deployed from the feature branch and clicked through.
6. **Approved PR** merged to `main`. Tag `main` to release to prod.

Treat the agent's PR like a teammate's PR. The goal isn't to distrust it. It's
that review is where you stay the owner of the system.

---

## 11. Phase 8: Retro (make the next session better)

At the end of each slice or session, ask:

> What did we learn that a future agent should know? Propose edits to AGENTS.md
> and the rules. Keep them short.

Typical outputs:

- a new gotcha line in `AGENTS.md`,
- a tightened rule (or a deleted one that never helped),
- a new skill if you repeated a multi-step procedure,
- a spec update so docs match reality.

This loop is how a harness gets better *for your project* over time.

---

## 12. Gaps in this repo

An audit of the current repo against this playbook:

| Gap | Impact | Fix |
|---|---|---|
| No `.cursor/rules` or `AGENTS.md` | The agent re-learns your policies each chat | Add both; copy from section 6 |
| No `.github/workflows` | Your preview/prod/approved-PR policy isn't enforced | Add preview, release, and PR-check workflows; enable branch protection |
| No automated tests | The agent can't verify logic changes | Start with unit tests for the SOFR, rating-gap and ranking logic |
| No `docs/spec.md` | The spec lives only in `DEMO_SCRIPT.md` and chat history | Extract a short per-persona spec with Done-when and Out-of-scope |
| Review screenshots in the repo (`.ew-review`, `.header-review`, `screenshots`) | Repo noise | Git-ignore or move out of the repo |
| `mlflow.db` and build artifacts near tracked code | Binary noise | Confirm they're git-ignored |

Suggested order: `AGENTS.md`, then rules, then CI, then tests. Each one
improves every later session.

---

## 13. Anti-patterns

| Anti-pattern | Why it hurts | Instead |
|---|---|---|
| "Build the whole app" in one prompt | Unreviewable, wrong in many places at once | Vertical slices with checks |
| Skipping Plan mode on big tasks | You find wrong direction after the code is written | Plan, review, then execute |
| Vague prompts ("make it better") | Agent fills gaps with generic choices | State the outcome and the check |
| No verification step | The agent claims success without proof | "Done when" plus evidence |
| One endless chat | Context rot, contradictions | One chat per slice; durable notes in files |
| Accepting diffs unread | You lose ownership of the system | Review contracts and config at minimum |
| Huge rule files | Skimmed, contradictory | Short, scoped, testable rules |
| Re-explaining the same thing | Wasted time | Put it in a rule or `AGENTS.md` |
| Letting the agent loop on a failure | Burns time, compounds damage | Stop after two tries and reset |
| Hardcoded ids and secrets | Breaks in a new workspace; security risk | One config object, bound resources, `.env` ignored |
| Debugging by guessing | Random changes | Evidence, hypotheses, one change at a time |

---

## 14. Prompt cheat sheet

**Interview me**
> Ask me the 5 to 8 questions that would most change the design. Use AskQuestion.
> No code yet.

**Plan**
> Plan only. Read @docs/spec.md and @app. Give ordered tasks, a verification
> step per task, dependencies, risks, and questions.

**Build a slice**
> Implement <slice>. Follow the pattern in @<example>. Don't touch <area>.
> Done when <check>. Show me the evidence.

**Match an existing pattern**
> Build the CFO screen using the same shell, components and data-fetching
> pattern as @routes/overview.tsx.

**Debug**
> Here is the exact error and logs: <paste>. List the 3 most likely causes and
> the cheapest check for each. Don't change code until we pick one.

**Review**
> Review the diff on this branch for bugs, regressions, and missing edge cases.
> Then run a security review on anything touching auth or data access.

**Retro**
> What did we learn that should go in AGENTS.md or a rule? Propose short edits.

**Reset a stuck chat**
> Summarize in 5 lines: the goal, what's done, what's broken, what we've tried,
> what we know. I'll paste it into a new chat.

---

## 15. Weekly habits

- After each feature: **one retro edit** to `AGENTS.md` or a rule.
- Before each feature: **write "Done when"** before you write the prompt.
- Each session: **commit at a clean checkpoint** before anything risky.
- Each week: **prune** rules and docs that no longer match the code.
- Keep a short list of **prompts that worked**. Reuse beats reinvention.

---

*Use this together with the architecture guide. This one tells you how to drive
the agent. The other tells you what to build.*
