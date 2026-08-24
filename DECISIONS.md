# Project Decision Log — Fraud-Spike Detector

Use this file to record decisions that affect evaluation, implementation, or the demo narrative. Make the choice once, record its rationale, and avoid silently changing it later.

## How to use this log

- Add a new row as soon as a decision is made; do not wait until the end of the day.
- Mark a decision **Proposed** until it is validated; mark it **Locked** once downstream work depends on it.
- If a locked decision must change, add a new row referencing the earlier one and state the impact on results.
- Keep values, seeds, and artifact paths precise enough for another person to reproduce the run.

## Decision register

| ID | Date | Area | Decision | Status | Rationale / evidence | Owner | Impacted artifacts |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-08-23 | Dataset | Use root-level `Paysim.csv` as the sole primary dataset. | Locked | Immediately available; 6,362,620 rows; 743 ordered simulation steps; complete transaction, balance, destination, and fraud-label fields. Declared upstream source: Kaggle PaySim, Version 2, CC BY-SA 4.0; local contents pinned by SHA-256 in data notes. PaySim is simulated, so results must not be presented as production merchant performance. | Project team | `Paysim.csv`, `reports/data_notes.md` |
| D-002 | 2026-08-23 | Canonical schema | Map `step` → `event_time`; `amount` → `amount`; `nameOrig` → `origin_account`; `nameDest` → `destination_account`; retain `type` and pre/post origin/destination balances as candidate features. Retain `isFraud` only for offline evaluation; exclude `isFlaggedFraud` from modeling. | Locked | These fields are complete and directly support chronological replay and behavioral features. `step` is a PaySim simulation time step (treated as an hourly replay clock). PaySim has no true IP, device, card-BIN, or geo fields; no claim will be made that it does. | Project team | `src/ingestion.py`, `src/features.py`, `reports/data_notes.md` |
| D-003 | 2026-08-23 | Time split | Use chronological splits: train = steps 1–520; validation = steps 521–631; held-out test = steps 632–743. | Locked | This is a 70/15/15 step-range split and preserves time order: train 6,082,007 rows / 5,781 fraud labels; validation 191,147 / 1,180; test 89,466 / 1,252. Test remains untouched until final frozen evaluation. The changing fraud rate over time will be documented as temporal distribution shift. | Project team | `src/ingestion.py`, `reports/data_notes.md`, `reports/metrics_report.md` |
| D-004 | 2026-08-23 | Synthetic labels | Use five fixed, offline-only fixtures: two validation and three test scenarios from the velocity-burst, amount-repetition, and destination-concentration families. Seed: `20260823`. Label every affected PaySim step as a positive synthetic-spike step; Day 3 will map step labels to scoring windows. | Locked | The source data has no native burst labels. Fixtures append clearly tagged synthetic events only to validation/test streams; training remains unmodified. Determinism is enforced by the fixed seed and automated tests. Scenario metadata and labels are persisted, but the generator is not a dashboard control. | Project team | `src/spike_injection.py`, `scripts/generate_synthetic_spikes.py`, `data/synthetic_spikes/`, `reports/synthetic_spike_notes.md` |
| D-005 | YYYY-MM-DD | Windows | _Choose window size and stride_ | Proposed | Balance detection latency, stable features, transaction volume, and visual clarity. |  | `src/features.py` |
| D-006 | YYYY-MM-DD | Features | _Freeze primary rolling features_ | Proposed | List each feature, entity level, lookback, null handling, and proof it uses no future data. |  | `src/features.py` |
| D-007 | YYYY-MM-DD | Baseline | _Choose EWMA/z-score configuration_ | Proposed | Explain fitting period and validation-only tuning method. |  | `src/models/baseline_zscore.py` |
| D-008 | YYYY-MM-DD | Primary model | _Choose Isolation Forest preprocessing and hyperparameters_ | Proposed | Record training subset, scaler fit scope, seed, and model version. |  | `src/models/isolation_forest.py` |
| D-009 | YYYY-MM-DD | Cost model | _Set illustrative FP/FN/TP cost assumptions_ | Proposed | Clearly label assumptions; state currency and source/reasoning. Never present estimates as merchant facts. |  | `src/evaluate.py`, `reports/metrics_report.md` |
| D-010 | YYYY-MM-DD | Operating point | _Select threshold from validation expected-cost minimum_ | Proposed | Record candidate range, selected configuration identifier, and comparison with max-F1 choice. Do not reveal raw operational threshold in UI. |  | model config, `reports/metrics_report.md` |
| D-011 | YYYY-MM-DD | Explainability | _Choose safe alert-reason language_ | Proposed | Use aggregate, bucketed reasons; exclude raw thresholds, weights, and evasion-relevant internals. |  | `src/explain.py`, `app/streamlit_app.py` |
| D-012 | YYYY-MM-DD | Demo scenario | _Freeze one deterministic replay scenario_ | Proposed | Record seed, duration, expected alert point, and fallback screenshot/video location. |  | `app/`, `reports/` |
| D-013 | YYYY-MM-DD | Final model | _Select model shown as primary in the demo_ | Proposed | Base this on held-out evidence, reliability, latency, and clarity—not novelty alone. |  | `reports/metrics_report.md`, README |

## Locked-decision checklist

- [x] Dataset selected; source and limitations documented.
- [x] Canonical schema mapped and ingestion reproducible.
- [x] Time split boundaries recorded; test set protected.
- [x] Injection seed and evaluation labels reproducible.
- [ ] Window size, stride, and feature schema frozen.
- [ ] Baseline and primary-model configurations recorded.
- [ ] Cost assumptions recorded and labeled illustrative.
- [ ] Operating point selected on validation only.
- [ ] Held-out test metrics generated after configuration freeze.
- [ ] Dashboard wording reviewed for defense-only safety.
- [ ] One deterministic demo scenario and backup recording ready.

## Change record

Add a row here only when changing a previously locked decision.

| Date | Replaces ID | What changed | Why | Revalidation required | Result |
|---|---|---|---|---|---|
| YYYY-MM-DD | D-___ |  |  |  |  |
