# Day 7 & Day 8: Evaluation, Explainability, & Streamlit Dashboard

This guide provides recommendations for running final evaluations, implementing explainable alerts, and building the Streamlit user interface.

---

## Day 7: Evaluation & Explainability

Once models and thresholds are frozen on the validation set, run a single final evaluation run on the untouched **held-out test set** split.

### Metrics to Calculate
Implement these in [`src/evaluate.py`](file:///Users/saksham/Desktop/RazorPay/src/evaluate.py):
*   **PR-AUC:** Precision-Recall AUC (critical for heavily imbalanced fraud data).
*   **ROC-AUC:** Reference metric.
*   **Precision, Recall, F1:** Traditional performance metrics.
*   **Detection Latency:** Time/step difference between the first synthetic injection step of a scenario and the step when the model first alerts.

### Explainability Module (`src/explain.py`)
To make alerts interpretable for risk managers, implement simple feature attribution. For tree-based models like `IsolationForest`, you can calculate how much each feature contributed to isolation or utilize a simple heuristic (e.g. deviation of the current feature value from the historical training mean).

*   **Constraint:** Respect the **defense-only design**. Do not expose raw thresholds or internal feature weights. Instead, output qualitative, bucketed risk reasons (e.g. "Spike in transaction velocity", "High repetitive activity") and relative contribution percentages.

```python
import pandas as pd

def explain_alert(window_features: pd.Series, train_means: dict, train_stds: dict) -> list[dict]:
    """Provide top contributing reasons for a flagged anomaly window without exposing raw numbers."""
    contributions = []
    # Identify which features are most standard deviations away from normal
    for col, mean in train_means.items():
        std = train_stds.get(col, 1.0)
        z = (window_features[col] - mean) / std
        if z > 2.0:
            contributions.append({"feature": col, "deviation": z})
            
    # Sort by standard deviation deviation
    sorted_reasons = sorted(contributions, key=lambda x: x["deviation"], reverse=True)[:3]
    
    # Translate features to natural language
    translation = {
        "event_count": "Sudden volume spike",
        "velocity_per_step": "High velocity burst",
        "repetition_ratio": "Highly repetitive behavior",
        "unique_destinations": "High volume of destinations"
    }
    
    return [
        {
            "signal": translation.get(r["feature"], r["feature"]),
            "contribution_level": "High" if r["deviation"] > 4.0 else "Medium"
        }
        for r in sorted_reasons
    ]
```

---

## Day 8: Streamlit Dashboard (`app/streamlit_app.py`)

Build a clean dashboard focusing on incident response.

### UI Flow
1.  **Replay Timeline:** Present a slider or button allowing the judge to replay the stream step-by-step.
2.  **Live Alerts Panel:** Display a table or set of cards listing active anomalies as they emerge in the transaction stream. Include:
    *   Time step flagged.
    *   Explainable reasons (from `src/explain.py`).
    *   Detection latency callout (e.g., "Caught within 2 steps of spike start").
3.  **Impact / Cost Metrics Tab:** Display the performance metrics on the held-out test split, including:
    *   The PR-AUC curve.
    *   The **Expected Cost vs. Threshold** chart (Plotly), highlighting the chosen operating point.
    *   A card explaining the cost savings compared to a simple max-F1 classifier.

### UI Safety Checklist
*   [ ] Ensure no diagnostic controls allow custom attack generation.
*   [ ] Confirm the cost curve has labels explicitly stating that the cost parameters are illustrative.
