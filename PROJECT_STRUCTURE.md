# Project Structure and Responsibilities

This repository is organized as a small, reproducible ML product: source data is preserved, derived artifacts are separated, model code is modular, and the Streamlit demo only consumes prepared outputs.

## Root files

| File | Responsibility |
|---|---|
| `README.MD` | Problem statement, architecture, judging narrative, and public project overview. |
| `HACKATHON_DEMO_PLAN.md` | The 10-day build schedule, definition of done, acceptance checks, and demo script. |
| `DECISIONS.md` | Durable log of dataset, split, feature, model, cost, and demo decisions. |
| `CODEX_WORKFLOW.md` | Daily Codex prompts, token-efficient working practices, and stack guidance. |
| `PROJECT_STRUCTURE.md` | This folder/file responsibility guide. |
| `Paysim.csv` | Immutable local source dataset. Ingestion reads it; no code overwrites it. |
| `pyproject.toml` | Python project metadata, runtime dependencies, developer tools, and test configuration. |
| `uv.lock` | Exact resolved dependency versions for reproducible installations. |
| `.env.example` | Safe template for future local configuration; contains no secrets. |

## Folders

| Folder | Responsibility |
|---|---|
| `data/raw/` | Optional location for source copies or future raw datasets. Keep raw data immutable. |
| `data/processed/` | Reproducible derived artifacts such as schema metadata, feature tables, and split summaries. |
| `data/synthetic_spikes/` | Offline-only seeded spike scenarios and their labels; never connected to dashboard controls. |
| `src/` | Reusable data, detection, evaluation, and explainability logic. No UI code. |
| `src/models/` | Independent detector implementations and their shared model conventions. |
| `app/` | Streamlit interface for replaying a frozen safe scenario and showing approved results. |
| `tests/` | Fast automated checks for data validation, leakage prevention, scoring, and reports. |
| `notebooks/` | One-off EDA or exploratory analysis; findings graduate into `src/` before use in the demo. |
| `reports/` | Human-readable evidence: data notes, final metrics, charts, screenshots, and methodology. |
| `scripts/` | Small explicit command-line entry points for reproducible project tasks. |

## Source and model files

| File | Responsibility |
|---|---|
| `src/ingestion.py` | Validate PaySim columns, normalize them to the canonical schema, sort by simulation time, apply locked time splits, and produce split metadata. |
| `src/spike_injection.py` | Create deterministic, offline-only synthetic spike labels for validation/test evaluation. |
| `src/features.py` | Build backward-looking, window-level features with leakage safeguards. |
| `src/models/baseline_zscore.py` | Explainable rolling statistical-control baseline. |
| `src/models/isolation_forest.py` | Primary unsupervised detector, training, scoring, and artifact loading. |
| `src/models/autoencoder.py` | Stretch-only comparison model; leave unused unless core acceptance checks are complete. |
| `src/evaluate.py` | Compute held-out metrics, alert grouping, latency, confusion matrix, and expected-cost curve. |
| `src/explain.py` | Convert model behavior into safe, aggregate alert reasons without revealing evasion details. |
| `app/streamlit_app.py` | Replay/Alerts/Impact views for judges; displays precomputed or safely derived outputs only. |
| `scripts/run_ingestion.py` | Command-line entry point that creates `data/processed/ingestion_summary.json`. |

## Test and report files

| File | Responsibility |
|---|---|
| `tests/conftest.py` | Shared test fixtures as the test suite grows. |
| `tests/test_ingestion.py` | Required-column, canonical-schema, sorting, and no-overlap split tests. |
| `tests/test_features.py` | Future tests proving rolling features do not inspect future transactions. |
| `tests/test_models.py` | Future detector training/scoring contract tests. |
| `tests/test_evaluate.py` | Future metric, latency, and cost-calculation tests. |
| `reports/data_notes.md` | Dataset provenance, schema, split counts, observations, and limitations. |
| `reports/synthetic_spike_notes.md` | Purpose, scope, label rule, and guardrails for offline-only synthetic evaluation fixtures. |
| `reports/metrics_report.md` | Frozen held-out results, cost assumptions, comparison, and honest limitations. |
| `data/processed/ingestion_summary.json` | Generated snapshot of the exact row counts, fraud labels, and boundaries for locked splits. |

## Placeholder files

`__init__.py` files make `src`, `src.models`, `app`, and `tests` importable Python packages. `.gitkeep` files preserve intentionally empty artifact directories in version control; they have no runtime behavior.
