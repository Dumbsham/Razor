"""Plot feature distributions for normal and spike windows."""

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="data/processed/validation/window_features_v1.csv")
    parser.add_argument("--output", default="reports/feature_distributions.png")
    return parser.parse_args()

def main():
    args = parse_args()
    features = pd.read_csv(args.features)
    
    if "is_synthetic_spike" not in features.columns:
        print("is_synthetic_spike column not found.")
        return
        
    spikes = features[features["is_synthetic_spike"] == True]
    normal = features[features["is_synthetic_spike"] == False]
    
    if spikes.empty:
        print("No synthetic spikes found in the provided feature dataset.")
        return
        
    cols_to_plot = ["event_count", "amount_mean", "velocity_per_step", "repetition_ratio"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Feature Distributions: Normal vs Spike Windows", fontsize=16)
    
    for i, col in enumerate(cols_to_plot):
        ax = axes[i // 2, i % 2]
        if col in features.columns:
            ax.hist(normal[col], bins=30, alpha=0.5, label="Normal", density=True)
            ax.hist(spikes[col], bins=30, alpha=0.5, label="Spike", density=True, color='red')
            ax.set_title(col)
            ax.legend()
            
    plt.tight_layout()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    print(f"Saved feature distribution plot to {output_path}")

if __name__ == "__main__":
    main()
