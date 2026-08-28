import numpy as np
import pandas as pd
from src.models.isolation_forest import IsolationForestModel
from sklearn.metrics import precision_score, recall_score, f1_score

train = pd.read_csv("data/processed/train/window_features_v1.csv").fillna(0)
val = pd.read_csv("data/processed/validation/window_features_v1.csv").fillna(0)
y_val = val["is_synthetic_spike"]

contaminations = [0.001, 0.005, 0.006, 0.01, 0.02, 0.05]
results = []
best_f1 = 0
best_params = {}

for contam in contaminations:
    model = IsolationForestModel(contamination=contam, random_state=42)
    model.fit(train)
    iso_scores = model.predict_scores(val)
    
    thresholds = np.linspace(iso_scores.min(), iso_scores.max(), 50)
    for t in thresholds:
        preds = iso_scores > t
        p = precision_score(y_val, preds, zero_division=0)
        r = recall_score(y_val, preds, zero_division=0)
        f1 = f1_score(y_val, preds, zero_division=0)
        
        results.append({
            "contamination": contam,
            "threshold": t,
            "precision": p,
            "recall": r,
            "f1": f1
        })
        
        if f1 > best_f1:
            best_f1 = f1
            best_params = {"contamination": contam, "threshold": t, "precision": p, "recall": r, "f1": f1}

df = pd.DataFrame(results)
df.to_csv("reports/sweep_results.csv", index=False)

print("Best Parameters:")
print(best_params)

# Print a P-R tradeoff table for the best contamination
best_c = best_params["contamination"]
print(f"\nPrecision-Recall tradeoff for best contamination ({best_c}):")
sub_df = df[df["contamination"] == best_c]
for _, row in sub_df.iterrows():
    if row["recall"] > 0:  # Only show where it catches at least something
        print(f"Thresh: {row['threshold']:.4f} | P: {row['precision']:.3f} | R: {row['recall']:.3f} | F1: {row['f1']:.3f}")

