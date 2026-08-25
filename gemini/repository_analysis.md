# Repository Analysis: Fraud-Spike Detector

This analysis details the current architectural state, file inventory, and implemented versus pending layers of the **Fraud-Spike Detector** project.

---

## 1. Directory Structure and Purpose

The repository is structured as a reproducible ML product.

| Path | Purpose / Responsibility | Current State |
|:---|:---|:---|
| [`README.MD`](file:///Users/saksham/Desktop/RazorPay/README.MD) | Public overview, problem statement, quickstart, system overview, evaluation plan, and demo narrative. | Complete |
| [`HACKATHON_DEMO_PLAN.md`](file:///Users/saksham/Desktop/RazorPay/HACKATHON_DEMO_PLAN.md) | 10-day build schedule, definitions of done, daily outcomes, and demo scripts. | Complete (Day 1 & Day 2 marked done) |
| [`DECISIONS.md`](file:///Users/saksham/Desktop/RazorPay/DECISIONS.md) | Architecture, dataset, and split decision logs. | Complete up to Decision D-004 |
| [`CODEX_WORKFLOW.md`](file:///Users/saksham/Desktop/RazorPay/CODEX_WORKFLOW.md) | Prompts, workflow guidelines, daily starts/ends, and token efficiency recommendations. | Complete |
| [`PROJECT_STRUCTURE.md`](file:///Users/saksham/Desktop/RazorPay/PROJECT_STRUCTURE.md) | Map of all directories and source/test file responsibilities. | Complete |
| `Paysim.csv` | Immutable source dataset (~493.5 MB, ~6.36M transactions). | Frozen / Immutable |
| `data/processed/` | Processed outputs. Contains `ingestion_summary.json`. | Generated |
| `data/synthetic_spikes/` | Injected scenarios, timelines, and ground truth validation/test step labels. | Generated |
| `src/` | ML pipeline logic (ingestion, features, evaluation, explainability). | Core implementation started |
| `src/models/` | Anomaly detectors. | Placeholders created |
| `app/` | Streamlit dashboard codebase. | Placeholder created |
| `tests/` | Unit tests. | 6 passing tests (ingestion, spikes) |
| `reports/` | Evidence reports (data notes, synthetic spike notes, metrics report). | Drafts / Notes completed |

---

## 2. Ingestion & Data Splits (Implemented)

[`src/ingestion.py`](file:///Users/saksham/Desktop/RazorPay/src/ingestion.py) successfully parses the raw `Paysim.csv` and builds canonical, time-sorted columns without leakage:

*   **Canonical Columns:** `event_time`, `transaction_type`, `amount`, `origin_account`, `origin_balance_before`, `origin_balance_after`, `destination_account`, `destination_balance_before`, `destination_balance_after`, and `is_fraud`.
*   **Time Splits:** Chronological partitions based on the simulation step (treated as an hourly clock):
    *   **Train:** Steps 1–520 (~6.08M rows)
    *   **Validation:** Steps 521–631 (~191K rows)
    *   **Test:** Steps 632–743 (~89K rows)

---

## 3. Synthetic Spike Injection (Implemented)

Since the original PaySim dataset has point-in-time fraud labels but lacks coordinated burst labels, [`src/spike_injection.py`](file:///Users/saksham/Desktop/RazorPay/src/spike_injection.py) injects deterministic, offline-only synthetic spike scenarios into the validation and test datasets:

1.  **Velocity Burst:** Rapid transactions in a brief interval.
2.  **Amount Repetition:** High frequency of identical transaction amounts.
3.  **Destination Concentration:** Multiple accounts directing funds to a single destination.

These are stored in `data/synthetic_spikes/` and mapped using a fixed seed (`20260823`) to ensure absolute reproducibility.

---

## 4. Current Progress & Missing Work

The progress of the 10-day execution plan stands as follows:

*   **[x] Day 1:** Ingestion and chronological splits.
*   **[x] Day 2:** Synthetic spike injection logic and fixtures.
*   **[ ] Day 3 (In Progress):** Window-level feature engineering. Code in `src/features.py` exists but tests in `tests/test_features.py` are empty and require verification.
*   **[ ] Day 4:** EWMA/z-score baseline model (`src/models/baseline_zscore.py` is empty).
*   **[ ] Day 5:** Primary Isolation Forest model (`src/models/isolation_forest.py` is empty).
*   **[ ] Day 6:** Cost-optimization model and threshold freezing (`src/evaluate.py` is empty).
*   **[ ] Day 7:** Held-out test evaluation and explainability (`src/explain.py` is empty, `reports/metrics_report.md` is empty/draft).
*   **[ ] Day 8:** Streamlit dashboard implementation (`app/streamlit_app.py` is empty).
*   **[ ] Day 9:** Rehearsal & Polishing.
*   **[ ] Day 10:** Final submission.
