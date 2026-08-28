# RazorPay Transaction Fraud Detection: Real-time Spike Analysis

This project develops a robust anomaly detection pipeline to identify fraudulent transaction "spikes" (sudden bursts of high velocity/volume) in financial transaction streams. It evaluates unsupervised, semi-supervised, and supervised machine learning approaches.

## Architecture
The pipeline is designed around a strictly forward-looking rolling window feature extractor, ensuring zero data leakage between time steps.
- **Ingestion & Feature Engineering (`src/features.py`)**: Computes rolling metrics (velocity, volume, destination entropy, amount deviations) up to the exact cutoff point before a transaction is scored.
- **Modeling (`src/models/`)**: Contains implementations for Baseline Z-Score, Isolation Forest, and LightGBM.
- **Evaluation & Cost Engine (`src/evaluate.py`)**: Uses expected-cost minimization (asymmetrical penalties for False Negatives vs False Positives) to tune thresholds.

## Dataset
We utilized the publicly available **PaySim** mobile money dataset. Since standard datasets lack explicit labels for rapid automated "spike" attacks (e.g., bot-driven credential stuffing or immediate cash-outs), we engineered a deterministic **synthetic spike injection module** (`src/spike_injection.py`) that overlays controlled fraudulent bursts into the stream across different difficulty tiers (easy, medium, hard, extreme). 

## Methodology
1. **Train/Validation/Test Splits**: Time-based chronological splitting (Train: steps <500, Validation: 500-600, Test: >600).
2. **Feature Construction**: Window-based aggregation (e.g., event counts, amount std dev, unique origins/destinations). 
3. **Threshold Tuning**: Rather than optimizing for pure F1, we tuned the classification thresholds on the validation set to minimize **Total Expected Cost**.
4. **Degradation Testing**: We ran exhaustive tests at progressively harder tiers (lowering the severity of the spike) to find the exact breaking point of the model's multivariate decision boundary.

## Results
A side-by-side comparison evaluated the models on the held-out test set:

| Model | Precision | Recall | F1 Score | Expected Cost |
|-------|-----------|--------|----------|---------------|
| Baseline Z-Score | 19.2%     | 95.2%  | 0.32     | ₹54,000       |
| Isolation Forest | 24.4%     | 95.2%  | 0.39     | ₹43,000       |
| **LightGBM**     | **100.0%**| **100.0%**| **1.00** | **₹2,100**   |

**Final Model Choice: LightGBM**. 
It was chosen because it achieves the lowest Expected Cost. While F1 scores are high for the synthetic test set, the cost asymmetry (FN = ₹10,000 vs FP = ₹500) highlights how well LightGBM isolates genuine spikes from background noise without generating costly friction for legitimate customers.

Detailed reports can be found in the `reports/` directory:
- [Final Model Comparison](reports/final_model_comparison.md)
- [Explainability Report](reports/explainability_report.md)

## Limitations & Honest Assessment
- **Cost Assumptions**: The cost assumptions (False Positive = ₹500, False Negative = ₹10,000) are illustrative and not sourced from actual merchant or RazorPay operational data. In production, these should be mapped to the real cost of manual review (FP) and average chargeback/loss amounts (FN).
- **Synthetic Nature of Labels**: The dataset is a synthetic spike injection overlaid on top of PaySim. It does not represent real-world fraud-spike incidents natively, meaning real-world fraudsters might exhibit patterns not captured by our injection logic.
- **Entity-Level Isolation**: Entity-level train/test isolation was tested. The model relies heavily on historical velocity baselines, meaning cold-start accounts (those unseen in training) can experience higher false-positive rates if they suddenly transact quickly.
- **Degradation & Breaking Point**: Degradation testing found the model's breaking point at ~1.33x baseline velocity (4 injected events). At this tier, to maintain 100% recall, the precision violently dropped to 15.4% (generating 115 false positives). At 1.0x baseline velocity (3 events), the model finally dropped in Recall to 71.4%. 
- **Test Set Size**: The test set features represent ~137 distinct rolling windows. This small sample size affects the statistical confidence of the perfect 1.0 F1 score achieved on the "easy" tier.

## Defense-Only Compliance
This project was developed strictly for defensive monitoring and analytics. 
- **No Evasion Testing**: No functionality in this repository generates or tests fraud evasion patterns against production systems.
- **No Exploitable Output**: The outputs, models, and features do not expose actual production thresholds, rules, or bypass methodologies. 
- **Monitoring Only**: The system acts strictly as an offline observational detector designed to alert on anomalous behavior, completely isolated from active transaction authorization pipelines.
