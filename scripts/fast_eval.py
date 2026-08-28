import sys
import pandas as pd
import numpy as np
import time
from src.ingestion import load_transactions
from src.spike_injection import inject_scenarios, SpikeScenario
from src.features import build_window_features
from src.models.lightgbm_detector import LightGBMDetector
from src.evaluate import evaluate_predictions, get_optimal_threshold, calculate_expected_costs

def run_tier(transactions, diff_name, counts):
    print(f"Running {diff_name}...", flush=True)
    t0 = time.time()
    scenarios = (
        SpikeScenario("train_velocity_01", "train", "velocity_burst", 150, 151, counts[0]),
        SpikeScenario("train_amount_01", "train", "amount_repetition", 250, 251, counts[1]),
        SpikeScenario("train_velocity_02", "train", "velocity_burst", 350, 351, counts[2]),
        SpikeScenario("train_destination_01", "train", "destination_concentration", 450, 451, counts[3]),
        SpikeScenario("validation_velocity_01", "validation", "velocity_burst", 545, 546, counts[4]),
        SpikeScenario("validation_amount_01", "validation", "amount_repetition", 590, 591, counts[5]),
        SpikeScenario("test_velocity_01", "test", "velocity_burst", 655, 656, counts[6]),
        SpikeScenario("test_amount_01", "test", "amount_repetition", 685, 686, counts[7]),
        SpikeScenario("test_destination_01", "test", "destination_concentration", 715, 716, counts[8]),
    )
    
    aug, labels = inject_scenarios(transactions, scenarios, strict_isolation=False)
    
    train_aug = aug[aug["event_time"] < 500]
    val_aug = aug[aug["event_time"].between(500, 600)]
    test_aug = aug[aug["event_time"] > 600]
    
    train_feat = build_window_features(train_aug, step_labels=labels).fillna(0)
    val_feat = build_window_features(val_aug, step_labels=labels).fillna(0)
    test_feat = build_window_features(test_aug, step_labels=labels).fillna(0)
    
    detector = LightGBMDetector()
    detector.fit(train_feat, train_feat["is_synthetic_spike"], val_feat, val_feat["is_synthetic_spike"])
    
    val_scores = detector.predict_scores(val_feat)
    thresholds = np.linspace(val_scores.min(), val_scores.max(), 50)
    cost_df = calculate_expected_costs(val_feat["is_synthetic_spike"], val_scores, thresholds, cost_fp=500.0, cost_fn=10000.0, cost_tp=100.0)
    optimal_thresh = get_optimal_threshold(cost_df)
    
    test_scores = detector.predict_scores(test_feat)
    test_preds = (test_scores >= optimal_thresh).astype(int)
    y_test = test_feat["is_synthetic_spike"]
    
    metrics = evaluate_predictions(y_test, test_preds, test_scores)
    
    pos_windows = test_feat[test_feat["is_synthetic_spike"] == True]
    neg_windows = test_feat[test_feat["is_synthetic_spike"] == False]
    
    avg_vel = pos_windows["max_entity_relative_velocity"].mean()
    min_pos_vel = pos_windows["max_entity_relative_velocity"].min()
    max_neg_vel = neg_windows["max_entity_relative_velocity"].max()
    
    print(f"Done {diff_name} in {time.time()-t0:.1f}s", flush=True)
    return {
        "tier": diff_name,
        "metrics": metrics,
        "avg_vel": avg_vel,
        "min_pos_vel": min_pos_vel,
        "max_neg_vel": max_neg_vel,
        "optimal_thresh": optimal_thresh
    }

def main():
    print("Loading transactions...", flush=True)
    transactions = load_transactions("Paysim.csv")
    print("Loaded.", flush=True)
    tiers = [
        ("easy", (120, 100, 120, 100, 120, 100, 120, 100, 100)),
        ("medium", (75, 50, 75, 50, 75, 50, 75, 50, 50)),
        ("hard", (25, 20, 25, 20, 25, 20, 25, 20, 20)),
        ("extreme", (8, 6, 8, 6, 8, 6, 8, 6, 6)),
    ]
    
    results = []
    for name, counts in tiers:
        res = run_tier(transactions, name, counts)
        results.append(res)
        
    print("\n\n--- RESULTS ---", flush=True)
    for r in results:
        m = r["metrics"]
        print(f"[{r['tier']}] Recall: {m['recall']:.3f}, P: {m['precision']:.3f}, F1: {m['f1']:.3f} | AvgVel: {r['avg_vel']:.2f} | MinPosVel: {r['min_pos_vel']:.2f} | MaxNegVel: {r['max_neg_vel']:.2f}", flush=True)

if __name__ == "__main__":
    main()
