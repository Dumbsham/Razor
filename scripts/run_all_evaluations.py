import sys
import pandas as pd
import numpy as np
import json
from pathlib import Path

from src.ingestion import load_transactions
from src.spike_injection import inject_scenarios, get_scenarios
from src.features import build_window_features
from src.models.lightgbm_detector import LightGBMDetector
from src.evaluate import calculate_expected_costs, get_optimal_threshold, evaluate_predictions

def main():
    transactions = load_transactions("Paysim.csv")
    
    difficulties = ["easy", "medium", "hard"]
    isolations = [False, True]
    
    results = {}
    
    for diff in difficulties:
        for strict in isolations:
            print(f"\\n--- Running: Difficulty={diff}, StrictIsolation={strict} ---")
            scenarios = get_scenarios(diff)
            aug, labels = inject_scenarios(transactions, scenarios, strict_isolation=strict)
            
            # Split ranges
            train_aug = aug[aug["event_time"] < 500]
            val_aug = aug[aug["event_time"].between(500, 600)]
            test_aug = aug[aug["event_time"] > 600]
            
            # Build features
            print("Building features...")
            train_feat = build_window_features(train_aug, step_labels=labels).fillna(0)
            val_feat = build_window_features(val_aug, step_labels=labels).fillna(0)
            test_feat = build_window_features(test_aug, step_labels=labels).fillna(0)
            
            # Train
            print("Training model...")
            detector = LightGBMDetector()
            detector.fit(train_feat, train_feat["is_synthetic_spike"], val_feat, val_feat["is_synthetic_spike"])
            
            # Val Threshold
            val_scores = detector.predict_scores(val_feat)
            thresholds = np.linspace(val_scores.min(), val_scores.max(), 50)
            cost_df = calculate_expected_costs(val_feat["is_synthetic_spike"], val_scores, thresholds, cost_fp=500.0, cost_fn=10000.0, cost_tp=100.0)
            optimal_thresh = get_optimal_threshold(cost_df)
            
            # Test Eval
            test_scores = detector.predict_scores(test_feat)
            test_preds = (test_scores >= optimal_thresh).astype(int)
            y_test = test_feat["is_synthetic_spike"]
            
            metrics = evaluate_predictions(y_test, test_preds, test_scores)
            
            # Calculate cost
            from sklearn.metrics import confusion_matrix
            cm = confusion_matrix(y_test, test_preds)
            tn, fp, fn, tp = cm.ravel() if len(cm.ravel()) == 4 else (cm[0,0], 0, 0, 0)
            cost = fp * 500.0 + fn * 10000.0 + tp * 100.0
            metrics["cost"] = cost
            metrics["cm"] = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
            
            print(metrics)
            
            key = f"{diff}_{'strict' if strict else 'normal'}"
            results[key] = metrics
            
            # Save report
            report_path = Path(f"reports/eval_{key}.json")
            report_path.parent.mkdir(exist_ok=True)
            report_path.write_text(json.dumps(metrics, indent=2))
            
    # Print summary table
    print("\\nFINAL SUMMARY")
    print("| Scenario | Isolation | Precision | Recall | F1 | PR-AUC | ROC-AUC | TP | FP | TN | FN | Cost |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    
    for diff in difficulties:
        for strict in isolations:
            key = f"{diff}_{'strict' if strict else 'normal'}"
            m = results[key]
            iso_str = "Strict" if strict else "Normal"
            print(f"| {diff} | {iso_str} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['pr_auc']:.3f} | {m['roc_auc']:.3f} | {m['cm']['tp']} | {m['cm']['fp']} | {m['cm']['tn']} | {m['cm']['fn']} | ${m['cost']:.2f} |")

if __name__ == "__main__":
    main()
