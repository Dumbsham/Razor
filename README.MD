# Fraud-Spike Detector

**Track 02 — AI Risk Manager | Razorpay Hackathon**
*Defense-only anomaly detection system for real-time transaction fraud spikes*

---

## 1. Problem Statement

Merchants on payment platforms lose money to three silent leaks: **fraud**, **returns**, and **chargebacks**. This project tackles one class of loss — **sudden, coordinated bursts of fraudulent transaction activity** (fraud spikes) — that are hard to catch with static, per-transaction rules but show up clearly as anomalies when transactions are viewed as a stream over time.

A fraud spike looks like:
- Many transactions from the same IP/device/card-BIN in a short time window
- Sudden deviation from a merchant's normal transaction velocity, amount distribution, or geography
- Clusters of near-identical transaction patterns appearing together

**Goal:** Build a system that monitors a transaction stream, flags anomalous spikes in near real-time, and reports honest precision/recall — including the **cost of false positives** — on a held-out test set.

**Constraint:** Strictly **defense-only**. The system must never expose logic that could help someone evade detection or construct a spike. No adversarial "how to bypass" outputs, no exposing raw detection thresholds/rules in a way that's exploitable by design.

---

## Quick Start

**Prerequisites:** Python 3.11+ and [uv](https://docs.astral.sh/uv/). Place `Paysim.csv` in the repository root; the file is intentionally read in place and never overwritten.

```bash
uv sync --all-groups
uv run python -m scripts.run_ingestion
uv run pytest -q
```

The ingestion command validates and normalizes the input, applies the locked chronological split, and writes `data/processed/ingestion_summary.json`. The Streamlit command will be added once the dashboard is implemented.

For data provenance, field definitions, splits, and limitations, see [`reports/data_notes.md`](reports/data_notes.md). For the build sequence, see [`HACKATHON_DEMO_PLAN.md`](HACKATHON_DEMO_PLAN.md).

---

## 2. Why This Sub-Track

- Fraud detection has strong public datasets (unlike return-risk or chargeback data, which need heavy synthetic assumptions for Indian e-commerce context).
- Rare-event detection + streaming anomaly scoring is a well-understood ML problem with mature baselines (Isolation Forest, statistical process control, autoencoders) — achievable in a 1.5-week window.
- Evaluation is clean: precision/recall/F1/ROC-AUC + a false-positive cost curve, which most competing teams are likely to skip — this is the differentiation.

---

## 3. System Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│  Transaction     │────▶│  Feature          │────▶│  Anomaly /         │────▶│  Alert +         │
│  Stream (real +  │     │  Engineering      │     │  Spike Detection   │     │  Cost Report     │
│  synthetic spikes)│     │  (windowed)       │     │  Model             │     │  (Streamlit UI)  │
└─────────────────┘     └──────────────────┘     └───────────────────┘     └─────────────────┘
```

### Pipeline stages

1. **Data ingestion** — historical/base dataset replayed as a time-ordered stream.
2. **Spike injection (synthetic)** — controlled bursts injected into held-out portions to create labeled ground truth for spike-level evaluation.
3. **Feature engineering** — rolling-window features per entity (IP, card-BIN, device, merchant) e.g. transaction count/velocity, amount z-score, entropy of destination merchants, time-since-last-transaction.
4. **Detection model** — unsupervised/semi-supervised anomaly scoring (Isolation Forest / rolling z-score + EWMA baseline, optionally a lightweight autoencoder as a stretch goal) producing a per-window anomaly score.
5. **Thresholding + alerting** — score → binary flag, tuned against the cost curve rather than a fixed default threshold.
6. **Evaluation** — precision, recall, F1, ROC-AUC/PR-AUC on held-out test windows, plus a **false-positive cost model**.
7. **Dashboard (Streamlit)** — visualize transaction stream, flagged spikes, and cost/metrics summary.

---

## 4. Dataset Strategy

| Source | Use |
|---|---|
| **Kaggle Credit Card Fraud (ULB)** | Base realistic transaction distribution + genuine fraud labels (highly imbalanced, ~0.17% fraud) |
| **PaySim (mobile money simulator)** | Alternative/supplementary — simulated but modeled on real velocity/amount patterns, easier to bucket into time windows |
| **Synthetic spike injection** | Since neither dataset has native "burst" labels, inject artificial coordinated bursts (same IP/device/amount cluster within a short window) into a held-out split to create spike-level ground truth |

**Split strategy:** Time-based split (not random) — train on earlier time windows, validate on a middle segment, and reserve a **strictly held-out, untouched final segment** for test metrics reporting. No leakage across windows used for feature computation (rolling windows must not peek into future data).

---

## 5. Feature Engineering (per entity, per rolling window)

- Transaction count in last N minutes
- Transaction velocity (Δcount / Δtime)
- Amount: mean, std, z-score vs entity's historical baseline
- Unique merchants/destinations touched in window
- Time-since-last-transaction (inter-arrival time)
- Entropy of transaction amounts/merchants (low entropy = repetitive/bot-like pattern)
- Geo/IP dispersion if available in dataset

---

## 6. Model Approach

**Baseline (must-have):**
- Rolling statistical control (z-score / EWMA) per entity — simple, explainable, fast to implement, good fallback

**Primary model:**
- Isolation Forest on windowed features — unsupervised, handles class imbalance naturally, doesn't require labeled fraud spikes to train

**Stretch (if time permits):**
- Lightweight autoencoder — reconstruction error as anomaly score
- Compare against baseline + Isolation Forest in final report (model comparison table adds credibility)

**Why not a supervised classifier as primary:** True spike-labeled data is scarce/synthetic; an unsupervised approach is more honest about what's actually learnable from this data, and is defensible when explaining methodology to judges.

---

## 7. Evaluation Plan

### Metrics (on held-out test set only)
- Precision, Recall, F1 (spike-level, not just point-level)
- ROC-AUC and PR-AUC (PR-AUC is more meaningful given class imbalance)
- Confusion matrix at chosen operating threshold
- Detection latency: how many transactions/minutes into a spike before it's flagged

### False-Positive Cost Model (the differentiator)
Assign explicit costs so the metric isn't just "accuracy":

| Outcome | Cost driver | Example cost logic |
|---|---|---|
| False Positive (genuine flagged as spike) | Customer friction, support load, merchant trust erosion | e.g. ₹X per flagged transaction in review/support overhead |
| False Negative (real spike missed) | Direct monetary fraud loss | e.g. ₹Y × average fraud transaction amount × count missed |
| True Positive | Saved loss minus review cost | Net benefit |

Report **total expected cost** at multiple thresholds and pick the threshold that minimizes expected cost — not the one that maximizes F1 blindly. Plot cost vs. threshold curve; this single chart is likely to be the strongest artifact in the submission.

### Explainability
For each flagged spike, surface the top contributing features (e.g. via feature attribution on the anomaly score) so the alert is interpretable, not a black box — reinforces "defense-only, transparent" positioning.

---

## 8. Defense-Only Compliance

- No output ever reveals exact thresholds, feature weights, or evasion-relevant internals in a way that's directly actionable for bypassing detection.
- No functionality that could be repurposed to generate fraud patterns or test evasion against real systems.
- Demo dashboard shows detection outcomes and aggregate explanations only — not a "tune your attack" interface.
- All synthetic spike generation code is clearly framed and used **only** for creating training/eval labels, not exposed as a user-facing tool.

---

## 9. Tech Stack

- **Language:** Python
- **Data/ML:** pandas, numpy, scikit-learn (Isolation Forest, preprocessing), optionally PyTorch/TensorFlow for autoencoder stretch goal
- **Evaluation:** scikit-learn metrics, matplotlib/plotly for cost curves
- **Dashboard:** Streamlit
- **Environment:** `uv` for Python package management

---

## 10. Repository Structure

```
fraud-spike-detector/
├── README.md
├── data/
│   ├── raw/                  # original downloaded datasets
│   ├── processed/            # windowed + feature-engineered data
│   └── synthetic_spikes/     # injected spike scenarios + labels
├── src/
│   ├── ingestion.py          # load + time-order transaction stream
│   ├── spike_injection.py    # synthetic burst generator
│   ├── features.py           # rolling-window feature engineering
│   ├── models/
│   │   ├── baseline_zscore.py
│   │   ├── isolation_forest.py
│   │   └── autoencoder.py    # stretch goal
│   ├── evaluate.py           # metrics + cost model
│   └── explain.py            # feature attribution for alerts
├── notebooks/
│   └── eda.ipynb
├── app/
│   └── streamlit_app.py      # dashboard
├── reports/
│   ├── metrics_report.md
│   └── cost_curve.png
└── requirements.txt
```

---

## 11. 1.5-Week Plan (6 hrs/day, ~63 hrs)

| Days | Focus | Hours |
|---|---|---|
| Day 1–2 | Dataset selection, EDA, time-based split, synthetic spike injection logic | 10–12 |
| Day 3–4 | Rolling-window feature engineering + baseline z-score model | 10 |
| Day 5–6 | Isolation Forest model, tuning, class-imbalance handling, cross-validation across time windows | 12 |
| Day 7 | Held-out test evaluation: precision/recall/F1/ROC-AUC/PR-AUC + false-positive cost modeling | 8 |
| Day 8 | Explainability (feature attribution) + Streamlit dashboard (stream view, alerts, metrics, cost chart) | 8 |
| Day 9 | Buffer, bug fixes, stretch goal (autoencoder comparison) if ahead of schedule | 6 |
| Day 10 | Demo narrative, deck, README/report polish, rehearse presentation | 6 |

---

## 12. Demo Narrative (for judges)

1. Show live/simulated transaction stream — mostly normal traffic.
2. Inject/replay a spike scenario — dashboard flags it with a latency callout ("detected within N transactions / M seconds").
3. Show the explanation panel — why this was flagged (top contributing features).
4. Switch to metrics tab — precision/recall/PR-AUC on held-out test set.
5. Show the **cost curve** — explain the threshold was chosen to minimize expected ₹ loss, not just to maximize F1.
6. Close with defense-only framing — no evasion-enabling outputs, transparent alerting only.

---

## 13. Open Questions / Assumptions to Validate Early

- Confirm whether Razorpay expects a specific dataset domain (payments-specific) vs. generic fraud datasets being acceptable — if unclear, state assumption explicitly in submission.
- Decide final cost-model numbers (₹ per false positive / false negative) — use illustrative but clearly-labeled assumptions if real merchant cost data isn't available; call this out transparently in the report rather than presenting invented numbers as fact.
- Decide whether PaySim or Kaggle Credit Card Fraud is the primary base dataset by end of Day 1 — don't run both in parallel past Day 2.
