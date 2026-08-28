# Day 5 & Day 6: Isolation Forest & Cost-Optimization Model

This guide details instructions on building the primary unsupervised model and optimizing its operational threshold using the expected cost curve.

---

## Day 5: Primary Isolation Forest Model

The primary anomaly detector in [`src/models/isolation_forest.py`](file:///Users/saksham/Desktop/RazorPay/src/models/isolation_forest.py) will use scikit-learn's `IsolationForest`. 

### Implementation Guide
1.  **Feature Selection:** Train the model on the rolling window features:
    *   `event_count`, `velocity_per_step`, `amount_mean`, `amount_std`, `amount_deviation`, `mean_interarrival_steps`, `unique_origins`, `unique_destinations`, `destination_entropy`, `amount_entropy`, `repetition_ratio`.
2.  **Fitting Contract:** Fit the `IsolationForest` exclusively on normal traffic windows from the training set. This is a semi-supervised/unsupervised setup.
3.  **Scoring:** Isolation Forest returns an anomaly score (lower means more anomalous). Invert this score or scale it so that higher scores represent higher risk:
    ```python
    # In scikit-learn: anomaly_score = -model.score_samples(X)
    ```
4.  **Save/Load Functions:** Implement persistence helpers to serialize the trained model and scaler to the disk (e.g. `data/processed/isolation_forest_v1.pkl`).

### Example Implementation Outline
```python
import pickle
from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class IsolationForestDetector:
    def __init__(self, contamination: float = 0.01, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.scaler = StandardScaler()
        self.feature_cols = [
            "event_count", "velocity_per_step", "amount_mean", "amount_std",
            "amount_deviation", "mean_interarrival_steps", "unique_origins",
            "unique_destinations", "destination_entropy", "amount_entropy", "repetition_ratio"
        ]

    def fit(self, train_features: pd.DataFrame):
        X = train_features[self.feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)

    def compute_anomaly_score(self, features: pd.DataFrame) -> pd.Series:
        X = features[self.feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)
        # score_samples returns negative anomaly score: lower values -> more anomalous.
        # Invert it so higher values indicate higher anomaly severity
        scores = -self.model.score_samples(X_scaled)
        return pd.Series(scores, index=features.index)

    def save(self, filepath: str | Path):
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str | Path) -> "IsolationForestDetector":
        with open(filepath, "rb") as f:
            return pickle.load(f)
```

---

## Day 6: Expected Business-Cost Model

Instead of maximizing standard F1 score, evaluate decisions using a business-focused **False-Positive Cost Model**. Implement this inside [`src/evaluate.py`](file:///Users/saksham/Desktop/RazorPay/src/evaluate.py).

### Cost Parameters (Illustrative Assumptions)
Define the economic impact of classification outcomes:
*   **False Positive (FP):** Cost of customer friction, review team overhead, and merchant support load (e.g., ₹500 per false alarm).
*   **False Negative (FN):** Value lost to missed fraud spikes (e.g., direct loss equal to 100% of transaction amounts inside the missed spike or a fixed penalty of ₹10,000 per missed scenario).
*   **True Positive (TP):** Net benefit (Saved loss minus a smaller review overhead).

### Threshold Optimization
1.  Iterate over candidate threshold values on the **validation set**.
2.  Calculate the total expected cost at each threshold:
    $$\text{Total Cost} = (\text{Count of FPs} \times \text{Cost}_{\text{FP}}) + (\text{Count of FNs} \times \text{Cost}_{\text{FN}}) + (\text{Count of TPs} \times \text{Cost}_{\text{TP}})$$
3.  Choose the threshold $T^*$ that minimizes the Total Cost.
4.  **Save this frozen threshold** and use it for evaluating the held-out test split.

### Cost Computation Signature
```python
def calculate_expected_costs(
    anomaly_scores: pd.Series,
    labels: pd.Series,
    thresholds: list[float],
    cost_fp: float = 500.0,
    cost_fn: float = 10000.0,
    cost_tp: float = 100.0
) -> pd.DataFrame:
    results = []
    for t in thresholds:
        preds = anomaly_scores > t
        tp = int(((preds == True) & (labels == True)).sum())
        fp = int(((preds == True) & (labels == False)).sum())
        fn = int(((preds == False) & (labels == True)).sum())
        tn = int(((preds == False) & (labels == False)).sum())
        
        total_cost = (fp * cost_fp) + (fn * cost_fn) + (tp * cost_tp)
        results.append({
            "threshold": t,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "total_cost": total_cost
        })
    return pd.DataFrame(results)
```
This ensures the selection of the operating point is backed by business logic rather than statistics alone.
