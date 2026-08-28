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
    
    print("\n--- Phase 3: LightGBM Detector ---")
    from src.models.lightgbm_detector import LightGBMDetector
    detector = LightGBMDetector()
    y_train = train["is_synthetic_spike"]
    detector.fit(train, y_train, val, y_val)
    detector.save(args.models_dir)
    
    lgb_scores = detector.predict_scores(val)
    
    # Calculate costs over range of thresholds
    thresholds = np.linspace(lgb_scores.min(), lgb_scores.max(), 50)
    cost_df = calculate_expected_costs(y_val, lgb_scores, thresholds, cost_fp=500.0, cost_fn=10000.0, cost_tp=100.0)
    
    optimal_thresh = get_optimal_threshold(cost_df)
    print(f"Optimal Threshold (Expected Cost): {optimal_thresh:.4f}")
    
    lgb_preds = lgb_scores > optimal_thresh
    lgb_metrics = evaluate_predictions(y_val, lgb_preds, lgb_scores)
    lgb_latency = calculate_latency(val, lgb_preds)
    
    print(f"LightGBM Metrics (Threshold={optimal_thresh:.4f}):")
    print(json.dumps(lgb_metrics, indent=2))
    print(f"LightGBM Latency: {lgb_latency}")
    
    # Save comparison report
    report = {
        "baseline_zscore": {
            "threshold": 3.0,
            "metrics": base_metrics,
            "latency": base_latency
        },
        "lightgbm": {
            "optimal_threshold": optimal_thresh,
            "metrics": lgb_metrics,
            "latency": lgb_latency
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
