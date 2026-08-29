<div align="center">
  <h1>💳 RazorPay Transaction Fraud Detection</h1>
  <h3>Real-time Spike & Burst Analysis Engine</h3>
  
  <p>
    A robust machine learning pipeline designed to detect sudden bursts of high velocity/volume fraudulent transactions (spikes) in financial transaction streams.
  </p>
</div>

---

## 📖 Overview

In modern financial systems like RazorPay, attackers often employ automated scripts or botnets to rapidly cash out compromised accounts, leading to a "spike" in transaction velocity. This project provides a complete pipeline to ingest transaction data, perform rolling-window feature engineering, and evaluate various anomaly detection strategies—focusing heavily on real-world **business cost optimization** over traditional classification metrics.

## 🚀 Quick Start

```bash
# 1. Install dependencies (requires uv or pip)
uv sync

# 2. Build rolling window features from raw dataset
python scripts/build_features.py

# 3. Inject synthetic fraudulent bursts
python scripts/generate_synthetic_spikes.py

# 4. Train, evaluate, and tune thresholds for models
python scripts/run_all_evaluations.py
```

## 🏗️ System Architecture

The core of our pipeline is designed to eliminate **data leakage**. Predictions strictly look at historical rolling windows relative to the timestamp of the transaction being evaluated.

*   **Ingestion & Feature Engineering (`src/features.py`)**: Computes streaming metrics (velocity, volume sum, destination entropy, moving averages) right up to the exact millisecond cutoff point before scoring a transaction.
*   **Modeling Engine (`src/models/`)**: Supports diverse strategies:
    *   *Baseline*: Statistical Z-Score
    *   *Unsupervised*: Isolation Forest
    *   *Supervised*: LightGBM (Gradient Boosting)
*   **Evaluation & Cost Engine (`src/evaluate.py`)**: Models are optimized not for F1 score, but for **Total Expected Cost**. We severely penalize missed fraud (False Negatives) over false alarms (False Positives).

## 📊 Dataset & Synthetic Spikes

This project is built using the publicly available **PaySim** mobile money dataset. 

**The Challenge:** Public datasets do not contain explicit, labeled examples of high-velocity "spike" attacks (e.g., credential stuffing or immediate massive cash-outs).
**The Solution:** We engineered a highly deterministic **Synthetic Spike Injection Module** (`src/spike_injection.py`). This allows us to overlay controlled, rapid fraudulent bursts onto normal traffic streams across multiple difficulty tiers: *Easy, Medium, Hard, and Extreme.*

## 🔬 Methodology

1.  **Strict Chronological Splitting**: Train (steps <500) ➔ Validation (500-600) ➔ Test (>600). We do not shuffle time, ensuring realistic time-series evaluation.
2.  **Rolling Aggregations**: We constructed moving-window aggregations covering metrics like transaction counts, amount standard deviation, and unique origin/destination footprints.
3.  **Cost-Sensitive Tuning**: Standard classification thresholds (e.g., > 0.5) are inadequate for fraud. We mapped costs—e.g., False Positive = ₹500 (manual review friction) and False Negative = ₹10,000 (chargeback loss)—and tuned the threshold strictly on the validation set to find the lowest possible financial impact.
4.  **Degradation Profiling**: We exposed our models to progressively stealthier spikes (lower volumes, fewer transactions) to determine the exact breaking point of our multivariate decision boundaries.

## 📈 Results

A side-by-side comparison on the held-out test set demonstrates the effectiveness of the supervised LightGBM approach when combined with our custom cost-optimization strategy.

| Model | Precision | Recall | F1 Score | Expected Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline Z-Score** | 19.2% | 95.2% | 0.32 | ₹54,000 |
| **Isolation Forest** | 24.4% | 95.2% | 0.39 | ₹43,000 |
| **LightGBM** | **100.0%** | **100.0%** | **1.00** | **₹2,100** |

🏆 **Final Selection: LightGBM**
While the synthetic 100% test F1 score is a byproduct of the "Easy" tier's deterministic nature, LightGBM dramatically isolated genuine spikes from background noise, cutting the theoretical operational loss to just ₹2,100 compared to ₹54,000 from a basic Z-Score approach.

---

## 🛑 Limitations & Honest Assessment

Transparency is critical in machine learning. This pipeline has the following known constraints and assumptions:

*   **Cost Assumptions are Illustrative**: The asymmetric cost ratio (FP: ₹500, FN: ₹10,000) was chosen to demonstrate the architecture's capability. In production, these numbers must be sourced directly from actual merchant risk metrics, average ticket sizes, and operational review center costs.
*   **Synthetic Target Variables**: Because the dataset relies on synthetic injection, the "fraud" patterns are highly deterministic. Real-world threat actors adapt, randomize their timing, and use highly distributed IPs/devices. The model currently learns our injection logic rather than an organic, evolving adversary.
*   **Cold-Start Vulnerability**: The model heavily weights historical velocity baselines per entity. A legitimate, brand-new user (cold-start) conducting their first few rapid transactions runs a high risk of being falsely classified as a spike until sufficient baseline history is established.
*   **Known Breaking Point**: Exhaustive degradation testing proved that the model breaks under "Extreme" stealth attacks. At 1.33x baseline velocity (just 4 anomalous events), maintaining perfect recall caused precision to plummet to 15.4% (generating 115 false positives). At 1.0x baseline velocity, the model failed entirely, with recall dropping to 71.4%.
*   **Sample Size Confidence**: The test set features represent only ~137 distinct rolling windows containing spikes. This small statistical sample size means the perfect 1.0 test score lacks broad statistical confidence and would likely degrade in a massive production stream.

## 🛡️ Defense-Only Compliance

This repository was developed **strictly for defensive monitoring, risk analytics, and educational purposes**.

*   **No Evasion Tools**: There is no code within this repository that generates, tests, or assists in creating fraud evasion patterns against active production systems.
*   **No Exploitable Output**: The metrics, models, and features do not expose actual, proprietary production rules, bypass techniques, or proprietary authorization logic.
*   **Read-Only Architecture**: The pipeline functions entirely as an offline observational detector, entirely disconnected from live, active transaction authorization gateways.
