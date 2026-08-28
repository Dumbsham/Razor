import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.models.isolation_forest import IsolationForestModel
from src.evaluate import evaluate_predictions, calculate_latency, calculate_expected_costs

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-features", default="data/processed/test/window_features_v1.csv")
    parser.add_argument("--models-dir", default="data/processed")
    parser.add_argument("--output-dir", default="reports")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("Loading test dataset (Held-out)...")
    test = pd.read_csv(args.test_features)
    test = test.fillna(0)
    
    if test.empty:
        print("Error: Empty test dataset.")
        return
        
    y_test = test["is_synthetic_spike"]
    
    print("Loading frozen model and threshold...")
    from src.models.lightgbm_detector import LightGBMDetector
    detector = LightGBMDetector.load(Path(args.models_dir) / "lightgbm.pkl")
    with open(Path(args.models_dir) / "optimal_threshold.json") as f:
        opt_thresh = json.load(f)["isolation_forest_threshold"]
        
    print(f"Optimal threshold loaded: {opt_thresh:.4f}")
    
    iso_scores = detector.predict_scores(test)
    iso_preds = iso_scores > opt_thresh
    
    metrics = evaluate_predictions(y_test, iso_preds, iso_scores)
    latency = calculate_latency(test, iso_preds)
    
    # Calculate costs to see what it would have been on test
    cost_fp=500.0
    cost_fn=10000.0
    cost_tp=100.0
    fp = metrics['fp']
    fn = metrics['fn']
    tp = metrics['tp']
    tn = metrics['tn']
    total_cost = (fp * cost_fp) + (fn * cost_fn) + (tp * cost_tp)
    metrics['total_cost'] = total_cost
    
    print("Test Metrics:")
    print(json.dumps(metrics, indent=2))
    print(f"Test Latency: {latency}")
    
    out_path = Path(args.output_dir) / "test_evaluation_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "threshold": opt_thresh,
        "metrics": metrics,
        "latency": latency
    }
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nSaved test report to {out_path}")
    
    # Generate the Markdown report
    md_report = f"""# Metrics Report

_Populate after the frozen pipeline is evaluated on the held-out test set._

## Methodology
- **Train**: Baseline and Isolation Forest fitting.
- **Validation**: Threshold selection to minimize expected cost.
- **Test**: Single held-out evaluation for final metrics reporting.

## Held-out results
- **Precision**: {metrics['precision']:.4f}
- **Recall**: {metrics['recall']:.4f}
- **F1 Score**: {metrics['f1']:.4f}
- **PR-AUC**: {metrics.get('pr_auc', 0):.4f}
- **ROC-AUC**: {metrics.get('roc_auc', 0):.4f}
- **Total Expected Cost**: ₹{total_cost:,.2f}

### Confusion Matrix
- True Negatives: {tn}
- False Positives: {fp}
- False Negatives: {fn}
- True Positives: {tp}

### Latency
{json.dumps(latency, indent=2)}

## Cost assumptions
- False Positive (FP) Cost: ₹500 (review time and potential customer friction).
- False Negative (FN) Cost: ₹10,000 (expected loss from a missed fraudulent burst).
- True Positive (TP) Cost: ₹100 (standard operational review cost).

## Limitations
- Synthetic labels do not perfectly capture the evolving nature of real-world fraud tactics.
- The model uses static historical features which might drift over time in a live environment.
- The false positive examples might include actual uncaught anomalous behavior from the underlying dataset.
"""

    md_path = Path("document") / "metrics_report.md"

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_report)
    print(f"Saved markdown report to {md_path}")

if __name__ == "__main__":
    main()
