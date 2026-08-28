# Project Progress: Days 1 to 3

This document provides a summary of the accomplishments from Day 1 to Day 3 for the Fraud-Spike Detector project. It details the purpose of each day, the roles of the corresponding files, and instructions on how to run and verify the implementation.

---

## Overview of the Days

### Day 1: Data Ingestion & Splits
**Goal:** Load the raw `Paysim.csv` dataset, apply a strict chronological split (train/validation/test), and ensure no data leakage between splits.
*   **What we did:** We defined canonical schemas to normalize the input data. We sorted the transactions strictly by `event_time` (the simulation step) and assigned steps 1–520 to Train, 521–631 to Validation, and 632–743 to Test.
*   **Why it matters:** In stream/time-series ML, random splits cause future data leakage. Chronological splitting ensures we train on the past and test on the future.

### Day 2: Synthetic Spike Injection
**Goal:** Create ground-truth labels for "coordinated fraud bursts."
*   **What we did:** Because the base dataset lacks labels for sudden, coordinated spikes, we built an offline injection script. It injects deterministic, labeled spike scenarios (e.g., velocity bursts, amount repetition, destination concentration) strictly into the validation and test splits using a fixed seed (`20260823`).
*   **Why it matters:** This allows us to calculate detection latency and evaluate if our model catches multi-transaction spikes, rather than just single fraudulent events. The training set remains purely un-injected.

### Day 3: Leakage-Safe Rolling Features
**Goal:** Convert the raw transaction stream into rolling-window features that a model can evaluate, strictly preventing future data leakage.
*   **What we did:** We compute window-level metrics (e.g., `event_count`, `velocity_per_step`, `amount_mean`, `unique_destinations`) for a target window `t` by looking only at history `[t - lookback_steps, t)`. We added rigorous assertions and `pytest` tests to guarantee that no future events contaminate the feature generation. Finally, we saved these processed features into CSVs for model training.

---

## File Roles & Architecture

| File Path | Role in the System |
| :--- | :--- |
| **`src/ingestion.py`** | Validates and normalizes raw columns. Splits data chronologically into train/validation/test sets. |
| **`scripts/run_ingestion.py`** | Script to execute ingestion and output a split summary report (`data/processed/ingestion_summary.json`). |
| **`tests/test_ingestion.py`** | Asserts canonical schema integrity and verifies the splits do not overlap. |
| **`src/spike_injection.py`** | Logic to generate deterministic fraud spikes and append them to transaction streams. |
| **`scripts/generate_synthetic_spikes.py`** | Script to inject spikes into validation/test splits and save labels to `data/synthetic_spikes/`. |
| **`tests/test_spike_injection.py`** | Tests to verify spikes are deterministic and preserve base rows. |
| **`src/features.py`** | Core engine for backward-looking feature engineering. Computes velocity, entropy, and z-scores over windows. |
| **`scripts/build_features.py`** | Script that loads splits, computes rolling features, and persists them into `data/processed/`. |
| **`scripts/plot_features.py`** | Generates EDA histograms comparing feature distributions of normal vs. spiked windows (`reports/feature_distributions.png`). |
| **`tests/test_features.py`** | Validates that window bounds strictly cut off before the scoring time, proving no future data leakage. |

---

## How to Run & Check the Project's Working

You can run the full Day 1–3 pipeline using `uv`. Follow these steps from the root directory of the repository:

### 1. Run Tests
Verify all logic (ingestion, synthetic spikes, and feature window leakage) is functioning correctly:
```bash
uv run pytest -q
```
*Expected Result:* All tests should pass. The `test_features.py` specifically guarantees that no future data leaks into current features.

### 2. Ingest the Data
Generate the chronological split summary:
```bash
uv run python -m scripts.run_ingestion
```
*Expected Result:* Outputs row counts and fraud rates for train, validation, and test splits. Saves a summary to `data/processed/ingestion_summary.json`.

### 3. Generate Synthetic Spikes
Inject evaluation ground truth into validation and test sets:
```bash
uv run python -m scripts.generate_synthetic_spikes
```
*Expected Result:* Generates scenarios and labels inside the `data/synthetic_spikes/` directory.

### 4. Build Window Features
Process the raw transaction splits into model-ready window feature datasets:
```bash
uv run python -m scripts.build_features
```
*Expected Result:* Will output `window_features_v1.csv` inside `data/processed/train/`, `data/processed/validation/`, and `data/processed/test/`.

### 5. Plot Sanity Checks
Visualize the distributions of the computed features to ensure spikes stand out:
```bash
uv run python -m scripts.plot_features
```
*Expected Result:* Generates a histogram grid at `reports/feature_distributions.png` showing how normal activity compares to synthetic spike activity.
