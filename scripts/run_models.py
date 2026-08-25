"""Train and evaluate models (Baseline & Isolation Forest) on Validation data."""

import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd

from src.models.baseline_zscore import BaselineZScoreModel
from src.models.isolation_forest import IsolationForestModel
from src.evaluate import evaluate_predictions, calculate_latency, calculate_expected_costs, get_optimal_threshold

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-features", default="data/processed/train/window_features_v1.csv")
    parser.add_argument("--val-features", default="data/processed/validation/window_features_v1.csv")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--models-dir", default="data/processed")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("Loading datasets...")
    train = pd.read_csv(args.train_features)
    val = pd.read_csv(args.val_features)
    
    if train.empty or val.empty:
        print("Error: Empty datasets.")
        return
        
    y_val = val["is_synthetic_spike"]
    
    # Ensure no NaNs
    train = train.fillna(0)
    val = val.fillna(0)

    print("\n--- Day 4: Baseline Z-Score Model ---")
    baseline = BaselineZScoreModel()
    baseline.fit(train)
    baseline.save(args.models_dir)
    
    baseline_scores = baseline.predict_scores(val)
    # Tune slightly: find a basic threshold on validation for baseline
    # E.g., threshold = 3.0
    baseline_preds = baseline.predict(val, threshold=3.0)
    
    base_metrics = evaluate_predictions(y_val, baseline_preds, baseline_scores)
    base_latency = calculate_latency(val, baseline_preds)
    
    print("Baseline Metrics (Threshold=3.0):")
    print(json.dumps(base_metrics, indent=2))
    print(f"Baseline Latency: {base_latency}")
    
    print("\n--- Day 5: Isolation Forest Model ---")
    iso_forest = IsolationForestModel(contamination=0.01, random_state=42)
    iso_forest.fit(train)
    iso_forest.save(args.models_dir)
    
    iso_scores = iso_forest.predict_scores(val)
    
    # Calculate costs over range of thresholds
    thresholds = np.linspace(iso_scores.min(), iso_scores.max(), 50)
    cost_df = calculate_expected_costs(y_val, iso_scores, thresholds, cost_fp=500.0, cost_fn=10000.0, cost_tp=100.0)
    
    optimal_thresh = get_optimal_threshold(cost_df)
    print(f"Optimal Threshold (Expected Cost): {optimal_thresh:.4f}")
    
    iso_preds = iso_scores > optimal_thresh
    iso_metrics = evaluate_predictions(y_val, iso_preds, iso_scores)
    iso_latency = calculate_latency(val, iso_preds)
    
    print(f"Isolation Forest Metrics (Threshold={optimal_thresh:.4f}):")
    print(json.dumps(iso_metrics, indent=2))
    print(f"Isolation Forest Latency: {iso_latency}")
    
    # Save comparison report
    report = {
        "baseline_zscore": {
            "threshold": 3.0,
            "metrics": base_metrics,
            "latency": base_latency
        },
        "isolation_forest": {
            "optimal_threshold": optimal_thresh,
            "metrics": iso_metrics,
            "latency": iso_latency
        }
    }
    
    out_path = Path(args.output_dir) / "validation_comparison_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nSaved validation report to {out_path}")
    
    # Save optimal threshold for test set evaluation (Day 7)
    thresh_path = Path(args.models_dir) / "optimal_threshold.json"
    thresh_path.write_text(json.dumps({"isolation_forest_threshold": optimal_thresh}))

if __name__ == "__main__":
    main()
