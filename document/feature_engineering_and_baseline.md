# Day 3 & Day 4: Feature Engineering & Baseline Model

This guide details the implementation steps and test-verification procedures for completing Day 3 and Day 4 of the hackathon plan.

---

## Day 3: Feature Verification and Safety Tests

Although [`src/features.py`](file:///Users/saksham/Desktop/RazorPay/src/features.py) is implemented, it has no tests in [`tests/test_features.py`](file:///Users/saksham/Desktop/RazorPay/tests/test_features.py). You must implement unit tests to verify:
1.  **No Future Data Leakage:** Ensure features for window starting at $t$ only consume transactions with $event\_time < t$.
2.  **Correct Aggregation Logic:** Validate the velocity calculation, z-score, unique accounts entropy, and repetitions.

### Implementation Checklist for `tests/test_features.py`
Create a test suite using `pytest` that:
*   Generates a dummy transaction DataFrame with controlled step times.
*   Calls `build_window_features` with a specific lookback/stride (e.g., lookback = 3, stride = 1).
*   Asserts that the outputs match manual calculations for amount mean, event count, and destination entropy.
*   Calls `assert_no_future_events` to prove safety.

```python
import pandas as pd
import pytest
from src.features import build_window_features, assert_no_future_events

def test_window_features_no_future_data_leakage():
    # Construct dummy transaction stream
    tx = pd.DataFrame({
        "event_time": [1, 2, 3, 4, 5],
        "amount": [10.0, 20.0, 30.0, 40.0, 50.0],
        "origin_account": ["A", "B", "A", "C", "B"],
        "destination_account": ["X", "Y", "X", "Z", "Y"]
    })
    
    features = build_window_features(tx, lookback_steps=3, stride_steps=1)
    
    # Verify bounds
    assert_no_future_events(features, tx)
    # The first window starts at min_step + lookback = 1 + 3 = 4
    # The history for window_start=4 must be steps 1, 2, 3
    row_t4 = features[features["window_start"] == 4].iloc[0]
    assert row_t4["event_count"] == 3
    assert row_t4["amount_mean"] == 20.0  # (10 + 20 + 30) / 3
```

Run tests using:
```bash
uv run pytest tests/test_features.py
```

---

## Day 4: Baseline EWMA / Z-Score Model

The baseline model [`src/models/baseline_zscore.py`](file:///Users/saksham/Desktop/RazorPay/src/models/baseline_zscore.py) should implement a simple, explainable anomaly detector using an Exponentially Weighted Moving Average (EWMA) or rolling statistical z-score on window features.

### Implementation Specifications
1.  **State Tracking:** Keep track of the historical mean and standard deviation of window feature metrics (like `amount_mean` or `velocity_per_step`) computed from the **training split only** to prevent leakage.
2.  **Scoring Function:** For any incoming window feature row, compute the z-score of the feature:
    $$Z = \frac{|x_t - \mu_{\text{train}}|}{\sigma_{\text{train}} + \epsilon}$$
3.  **Thresholding & Alert Grouping:**
    *   Flag any window with $Z > \text{threshold}$ as an anomaly.
    *   Group contiguous flagged windows into alert blocks to determine the detection latency.

### Outline for `src/models/baseline_zscore.py`
```python
import numpy as np
import pandas as pd

class BaselineZScoreModel:
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
        self.feature_means = {}
        self.feature_stds = {}

    def fit(self, train_features: pd.DataFrame):
        # Calculate mean and std on train features to avoid leakage
        for col in ["event_count", "amount_mean", "velocity_per_step", "repetition_ratio"]:
            self.feature_means[col] = train_features[col].mean()
            self.feature_stds[col] = train_features[col].std(ddof=0)

    def score(self, features: pd.DataFrame) -> pd.Series:
        # Compute aggregate z-scores (max z-score across target features)
        scores = []
        for _, row in features.iterrows():
            row_z = []
            for col in self.feature_means:
                mean = self.feature_means[col]
                std = self.feature_stds[col] if self.feature_stds[col] > 0 else 1e-5
                z = abs(row[col] - mean) / std
                row_z.append(z)
            scores.append(max(row_z))
        return pd.Series(scores, index=features.index)

    def predict(self, features: pd.DataFrame) -> pd.Series:
        scores = self.score(features)
        return scores > self.threshold
```

Write unit tests in [`tests/test_models.py`](file:///Users/saksham/Desktop/RazorPay/tests/test_models.py) to confirm:
*   Fitting occurs only on training data.
*   The baseline predicts anomalies deterministically.
