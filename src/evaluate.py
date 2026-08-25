"""Evaluation metrics, latency calculation, and cost optimization."""

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score, roc_auc_score, confusion_matrix

def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series, y_score: pd.Series = None) -> dict:
    """Calculate standard classification metrics for the window predictions."""
    metrics = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    
    cm = confusion_matrix(y_true, y_pred, labels=[False, True])
    metrics["tn"] = int(cm[0, 0])
    metrics["fp"] = int(cm[0, 1])
    metrics["fn"] = int(cm[1, 0])
    metrics["tp"] = int(cm[1, 1])
    
    if y_score is not None and len(np.unique(y_true)) > 1:
        metrics["pr_auc"] = float(average_precision_score(y_true, y_score))
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
    else:
        metrics["pr_auc"] = None
        metrics["roc_auc"] = None
        
    return metrics


def calculate_latency(features: pd.DataFrame, predictions: pd.Series) -> dict:
    """Calculate the detection latency for each injected scenario.
    
    Returns a dictionary mapping scenario_id to the number of steps 
    it took to detect it (or None if missed).
    """
    df = features.copy()
    df["pred"] = predictions
    
    latencies = {}
    
    # Identify unique scenarios from the scenario_ids column
    all_scenarios = set()
    for ids in df["scenario_ids"].dropna().unique():
        if ids:
            all_scenarios.update(ids.split(","))
            
    for scenario in all_scenarios:
        # Find all windows that are part of this scenario
        scenario_mask = df["scenario_ids"].astype(str).str.contains(scenario, regex=False)
        scenario_windows = df[scenario_mask].sort_values("window_start")
        
        if scenario_windows.empty:
            continue
            
        first_spike_step = scenario_windows["window_start"].min()
        
        # Find the first window where the model predicted True
        detections = scenario_windows[scenario_windows["pred"] == True]
        
        if not detections.empty:
            first_detection_step = detections["window_start"].min()
            latency = int(first_detection_step - first_spike_step)
            latencies[scenario] = max(0, latency)
        else:
            latencies[scenario] = None # Missed
            
    return latencies


def calculate_expected_costs(
    y_true: pd.Series, 
    y_score: pd.Series, 
    thresholds: np.ndarray,
    cost_fp: float = 500.0,
    cost_fn: float = 10000.0,
    cost_tp: float = 100.0
) -> pd.DataFrame:
    """Evaluate the expected business cost across a range of thresholds.
    
    - FP: Cost of reviewing a false alarm / friction.
    - FN: Cost of missing a fraud spike (losses).
    - TP: Cost of reviewing a true alarm (usually much smaller than FN).
    """
    results = []
    
    for t in thresholds:
        y_pred = y_score > t
        cm = confusion_matrix(y_true, y_pred, labels=[False, True])
        tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
        
        total_cost = (fp * cost_fp) + (fn * cost_fn) + (tp * cost_tp)
        
        results.append({
            "threshold": t,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "total_cost": total_cost,
            "f1": float(f1_score(y_true, y_pred, zero_division=0))
        })
        
    return pd.DataFrame(results)

def get_optimal_threshold(cost_df: pd.DataFrame) -> float:
    """Return the threshold that minimizes the total expected cost."""
    min_cost_idx = cost_df["total_cost"].idxmin()
    return float(cost_df.loc[min_cost_idx, "threshold"])
