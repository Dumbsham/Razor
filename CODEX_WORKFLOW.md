# Efficient Codex Workflow — Fraud-Spike Detector

This is a prompt and operating guide for building the project in small, verifiable increments while keeping context and token use low.

## Working tech stack

| Layer | Choice | Purpose |
|---|---|---|
| Language/runtime | Python 3.11+ | Core application and analysis code |
| Dependency management | `uv` | Reproducible environment and fast commands |
| Data processing | pandas, NumPy | Ingestion, transformations, rolling features |
| ML | scikit-learn | Isolation Forest, preprocessing, metrics |
| Baseline | Custom Python EWMA/z-score | Explainable streaming comparison |
| Charts | Plotly (dashboard) + Matplotlib (saved reports) | Interactive demo charts and reproducible artifacts |
| App | Streamlit | Local judge-facing replay dashboard |
| Testing | pytest | Leakage, feature, and pipeline regression checks |
| Quality | Ruff (optional but recommended) | Fast linting/formatting |
| Documentation | Markdown | README, decisions, metrics, and demo notes |

**Explicit non-goals for this 10-day build:** Kafka, database infrastructure, cloud deployment, authentication, an autoencoder, and a real payments integration. Add only after the core demo is finished and reproducible.

## The compact daily start prompt

Paste this at the beginning of each work session. Replace text in brackets only.

```text
We are building the Fraud-Spike Detector in this repository. Read only README.MD, HACKATHON_DEMO_PLAN.md, DECISIONS.md, and the files directly relevant to today’s task. Do not scan the whole repository.

Today is Day [N]. Goal: [one concrete outcome].
Acceptance check: [one observable check].
Relevant files: [paths, or “discover only under src/<area>”].

First, report in at most 6 bullets: current relevant state, blockers, and the smallest implementation plan. Then implement only this goal. Preserve unrelated changes. Use apply_patch for edits, run the narrowest relevant verification, update DECISIONS.md if a decision is made, and finish with: changed files, verification result, remaining risk, and exact next task. Do not add stretch features or ask follow-up questions unless blocked by a material decision.
```

### Example: Day 3

```text
We are building the Fraud-Spike Detector in this repository. Read only README.MD, HACKATHON_DEMO_PLAN.md, DECISIONS.md, src/ingestion.py, and files under src/ relevant to features. Do not scan the whole repository.

Today is Day 3. Goal: create leakage-safe backward-looking rolling window features and persist a versioned processed dataset.
Acceptance check: each feature row can be proven to use only events earlier than its scoring window, and a narrow test enforces that rule.
Relevant files: src/features.py, src/ingestion.py, tests/.

First, report in at most 6 bullets: current relevant state, blockers, and the smallest implementation plan. Then implement only this goal. Preserve unrelated changes. Use apply_patch for edits, run the narrowest relevant verification, update DECISIONS.md if a decision is made, and finish with: changed files, verification result, remaining risk, and exact next task. Do not add stretch features or ask follow-up questions unless blocked by a material decision.
```

## The compact daily end prompt

Use this after implementation, or when resuming a session where work may have been partially completed.

```text
Perform a concise end-of-day review for the Fraud-Spike Detector. Read git status plus only the files changed today and the relevant entries in DECISIONS.md/HACKATHON_DEMO_PLAN.md. Do not modify source code unless a verification failure has a small, obvious fix.

Return:
1. completed checklist items;
2. files changed and why;
3. commands run and pass/fail results;
4. decisions made or still needed;
5. risks/debt that could affect the demo;
6. the single highest-value first task for tomorrow.

Keep it under 350 words. If a plan checkbox is complete, update HACKATHON_DEMO_PLAN.md; if a decision was made, update DECISIONS.md.
```

## Focused task prompts

Use one of these instead of a broad “build the app” request.

### Implement one unit of work

```text
Implement [specific function/page/model step] only. Before editing, inspect [exact paths]. Keep the public interface [name/signature] unless there is a documented reason to change it. Add or update the narrowest test. Do not refactor unrelated code. Verify with [exact command]. Summarize in 120 words or fewer.
```

### Diagnose a failure

```text
Diagnose this failure without changing code yet: [error/output]. Inspect only the traceback paths, relevant config, and their direct dependencies. Give the most likely root cause, evidence, and the smallest safe fix. Do not propose broad rewrites.
```

### Review before a demo

```text
Review the Fraud-Spike Detector for a hackathon demo. Inspect README.MD, reports/metrics_report.md, app/streamlit_app.py, and changed files only. Check reproducibility, leakage claims, metric provenance, UX clarity, and defense-only safety. Return prioritized findings with file/line references. Do not edit files.
```

## Practices that save time and tokens

1. **One outcome per prompt.** Ask for “implement leakage test for feature rows,” not “finish ML pipeline.” Smaller requests need less repository reading and produce safer edits.
2. **Name the allowed files.** Start with 3–6 paths. Ask Codex to discover only inside one directory when exact names are unknown.
3. **Give an acceptance test.** A concrete success condition prevents long exploratory discussion and makes verification automatic.
4. **Request narrow commands.** Prefer one unit test, one script, or one page startup over “run everything” until integration day.
5. **Keep durable context in files.** Put decisions in `DECISIONS.md`, results in `reports/metrics_report.md`, and current plan state in `HACKATHON_DEMO_PLAN.md`; then prompts can refer to them instead of repeating history.
6. **Ask for a bounded response.** “At most 6 bullets” or “under 150 words” limits status chatter without limiting implementation quality.
7. **Separate diagnosis from fixing.** First ask for evidence and smallest fix when an error is unfamiliar; then authorize the fix in the next prompt.
8. **Protect the demo scope.** Include “do not add stretch features” in daily prompts. The biggest hackathon risk is spending hours on an impressive but unverified extra model.
9. **Use Codex for checkpoints.** At the end of each day, request the concise review above and update the plan/decision log while the rationale is fresh.
10. **Preserve reproducibility.** Tell Codex to log seeds, split boundaries, versions, and artifact paths immediately when they are chosen.

## Prompt anti-patterns

| Avoid | Better request |
|---|---|
| “Build the whole fraud detector.” | “Implement chronological splitting in `src/ingestion.py`; test no overlap; report row counts.” |
| “Look through the repo and fix things.” | “Inspect `app/streamlit_app.py` and its imports; diagnose why startup fails.” |
| “Make the model better.” | “Compare baseline and Isolation Forest on frozen validation data; change nothing; identify the top two error patterns.” |
| “Use the best model.” | “Keep the frozen scope; only evaluate an autoencoder if all Day 7 checks pass.” |
| “Give me an update.” | “Return progress, verification, blocker, and next task in ≤150 words.” |

## Suggested daily rhythm

| Moment | Action |
|---|---|
| First 10 minutes | Paste the daily start prompt, state one outcome and acceptance check. |
| During implementation | Issue focused prompts for one function, test, or page at a time. Keep outputs brief. |
| After a material choice | Ask Codex to update the exact row in `DECISIONS.md` with rationale and impact. |
| Last 15 minutes | Paste the daily end prompt, update checklists, and save a clean runnable state. |

## Safety and credibility reminders

- Never ask to expose exact detection thresholds, feature weights, raw rule logic, or synthetic-spike controls in the dashboard.
- Keep synthetic generation offline and framed strictly as an evaluation-labeling mechanism.
- Ask Codex to distinguish measured results from illustrative cost assumptions in every report and UI text.
- Require a time-based split and leakage test before accepting model metrics as demo evidence.
