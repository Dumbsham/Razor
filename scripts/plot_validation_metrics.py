import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, confusion_matrix

from src.models.isolation_forest import IsolationForestModel
from src.evaluate import calculate_expected_costs

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--val-features", default="data/processed/validation/window_features_v1.csv")
    parser.add_argument("--models-dir", default="data/processed")
    parser.add_argument("--output-dir", default="reports")
    return parser.parse_args()

def main():
    args = parse_args()
    val = pd.read_csv(args.val_features).fillna(0)
    y_val = val["is_synthetic_spike"]
    
    iso_forest = IsolationForestModel.load(Path(args.models_dir) / "isolation_forest.pkl")
    iso_scores = iso_forest.predict_scores(val)
    
    with open(Path(args.models_dir) / "optimal_threshold.json") as f:
        opt_thresh = json.load(f)["isolation_forest_threshold"]
    
    # 1. Cost vs Threshold
    thresholds = np.linspace(iso_scores.min(), iso_scores.max(), 100)
    cost_df = calculate_expected_costs(y_val, iso_scores, thresholds)
    
    plt.figure(figsize=(10, 6))
    plt.plot(cost_df["threshold"], cost_df["total_cost"], label="Total Expected Cost")
    plt.axvline(opt_thresh, color="red", linestyle="--", label=f"Optimal Threshold ({opt_thresh:.2f})")
    plt.xlabel("Anomaly Score Threshold")
    plt.ylabel("Expected Cost (₹)")
    plt.title("Expected Cost vs Threshold (Validation)")
    plt.legend()
    plt.savefig(Path(args.output_dir) / "validation_cost_vs_threshold.png")
    plt.close()
    
    # 2. Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_val, iso_scores)
    plt.figure(figsize=(10, 6))
    plt.plot(recall, precision, marker=".", label="Isolation Forest")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve (Validation)")
    plt.legend()
    plt.savefig(Path(args.output_dir) / "validation_pr_curve.png")
    plt.close()

if __name__ == "__main__":
    main()
