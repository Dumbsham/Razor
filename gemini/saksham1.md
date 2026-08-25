# Progress: Day 4 & Day 5

This document explains what was achieved during Day 4 and Day 5 of the Hackathon plan, detailing how we built our anomaly detectors and optimized them using a business-focused cost model.

---

## 🚀 What We Achieved

### Day 4: Baseline Model 
**Goal:** Build a simple, explainable baseline anomaly detector to establish a comparison point.
*   **What we did:** We implemented a "Z-Score" model that tracks the average behavior (mean and standard deviation) of the features observed in the *training* data. When new windows arrive in the *validation* data, the model computes how far they deviate from the training average. If a feature deviates by more than a chosen threshold (e.g., 3.0 standard deviations), it is flagged as an anomaly.
*   **Why it matters:** Advanced machine learning models (like Isolation Forests) need to prove their worth. The Baseline model provides a naïve metric benchmark to show that our advanced model actually offers significant value.

### Day 5: Primary Anomaly Detector
**Goal:** Build the robust, unsupervised machine learning model (`IsolationForest`) and optimize it mathematically.
*   **What we did:** We implemented scikit-learn's `IsolationForest`, fitting it on the training data. This model is exceptionally good at finding strange data distributions without needing explicitly labeled fraud in the training set. 
*   **How we picked the threshold:** Instead of maximizing statistical metrics like "F1-Score", we built an **Expected Cost Model**. We simulated the business costs:
    *   **False Positive (FP):** ₹500 (friction and manual review cost).
    *   **False Negative (FN):** ₹10,000 (direct monetary loss of missing a fraud spike).
    *   Since missing a spike is extremely expensive compared to investigating a false alarm, our model learned to choose a threshold (`0.4118`) that drastically prioritizes catching every spike, minimizing the total monetary cost to the business.

---

## 📂 File Roles & Architecture

Here is the breakdown of the files we built and what each does:

| File Path | Role in the System |
| :--- | :--- |
| **`src/models/baseline_zscore.py`** | The logic for the baseline model. It learns the standard deviation and mean for each feature on normal transactions and scores anomalies dynamically based on deviations. |
| **`src/models/isolation_forest.py`** | The logic for the primary machine learning model. It scales the features and isolates abnormal windows using tree partitions. |
| **`src/evaluate.py`** | Our evaluation engine. It computes standard metrics (Precision, Recall, F1), calculates **detection latency** (how fast a spike was caught), and contains the business logic for the **Expected Cost Model** which calculates the total ₹ impact of our thresholds. |
| **`scripts/run_models.py`** | The execution script. It loads the processed feature datasets, trains both models, scores them on the validation split, calculates the optimal threshold, and saves the comparison report. |
| **`data/processed/isolation_forest.pkl`** | The serialized version of our trained Isolation Forest model and its scaler, ready to be loaded by the Streamlit dashboard in real-time. |
| **`data/processed/optimal_threshold.json`** | The saved threshold value (`0.4118`) which mathematically minimizes the financial cost. |
| **`reports/validation_comparison_report.json`** | The final metrics comparison output highlighting that Isolation Forest vastly outperformed the baseline approach on the validation split. |

---

## 🛠 How to Run & Verify Models

You can train both models, calculate latency, run the cost-optimization loop, and output the validation reports using a single script:

```bash
uv run python -m scripts.run_models
```

**Expected Result:**
The script will output metrics for the Baseline Model and then for the Isolation Forest Model. It will print the newly found `Optimal Threshold (Expected Cost)` and display the exact detection latencies (how many steps it took to catch a given scenario) for both models. All parameters and performance reports will be saved into `data/processed/` and `reports/`.
