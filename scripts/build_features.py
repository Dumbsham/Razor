"""Generate rolling-window features for each time split and persist them."""

import argparse
from pathlib import Path
import pandas as pd

from src.ingestion import load_transactions, split_transactions
from src.features import build_window_features, assert_no_future_events, persist_feature_dataset

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="Paysim.csv")
    parser.add_argument("--labels", default="data/synthetic_spikes/spike_step_labels.csv")
    parser.add_argument("--output-dir", default="data/processed")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("Loading transactions...")
    transactions = load_transactions(args.input)
    splits = split_transactions(transactions)
    
    labels_path = Path(args.labels)
    if labels_path.exists():
        step_labels = pd.read_csv(labels_path)
    else:
        step_labels = None
        print(f"Warning: No synthetic labels found at {args.labels}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for split_name, split_df in splits.items():
        print(f"Building features for {split_name} split ({len(split_df)} rows)...")
        if split_df.empty:
            continue
            
        split_labels = step_labels[step_labels["split"] == split_name] if step_labels is not None else None
        
        features = build_window_features(split_df, step_labels=split_labels)
        assert_no_future_events(features, split_df)
        
        split_dir = output_dir / split_name
        data_path, metadata_path = persist_feature_dataset(features, split_dir)
        print(f"  -> Saved {len(features)} windows to {data_path}")

if __name__ == "__main__":
    main()
