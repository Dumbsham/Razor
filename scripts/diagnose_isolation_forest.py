import pandas as pd
import numpy as np
from src.models.isolation_forest import IsolationForestModel

train = pd.read_csv("data/processed/train/window_features_v1.csv").fillna(0)
val = pd.read_csv("data/processed/validation/window_features_v1.csv").fillna(0)
test = pd.read_csv("data/processed/test/window_features_v1.csv").fillna(0)

# 4. Report set sizes
print("=== 4. Dataset Sizes ===")
print("Validation set:")
print(f"Total: {len(val)}")
print(f"Positive (Spike): {val['is_synthetic_spike'].sum()}")
print(f"Negative (Normal): {len(val) - val['is_synthetic_spike'].sum()}")

print("\nTest set:")
print(f"Total: {len(test)}")
print(f"Positive (Spike): {test['is_synthetic_spike'].sum()}")
print(f"Negative (Normal): {len(test) - test['is_synthetic_spike'].sum()}")

# 1. Summary stats of anomaly scores on validation set
print("\n=== 1. Anomaly Score Distribution (Validation) ===")
# Use the same model as in training script (contamination doesn't matter for predict_scores)
model = IsolationForestModel(contamination=0.01, random_state=42)
model.fit(train)
val['anomaly_score'] = model.predict_scores(val)

val_spikes = val[val['is_synthetic_spike'] == True]
val_normal = val[val['is_synthetic_spike'] == False]

def print_stats(series, name):
    print(f"\n{name} Stats:")
    print(f"Min:    {series.min():.5f}")
    print(f"Max:    {series.max():.5f}")
    print(f"Mean:   {series.mean():.5f}")
    print(f"Median: {series.median():.5f}")

print_stats(val_spikes['anomaly_score'], "True Positive (Spike) Samples")
print_stats(val_normal['anomaly_score'], "True Negative (Normal) Samples")

# 3. Feature values comparison
print("\n=== 3. Raw Feature Values Comparison ===")
features = model.feature_columns
# Pick 3 random normal and 3 random spike samples
sample_spikes = val_spikes.sample(n=3, random_state=42)[features]
sample_normal = val_normal.sample(n=3, random_state=42)[features]

print("\nSpike Samples (3 rows):")
print(sample_spikes.T.to_string())

print("\nNormal Samples (3 rows):")
print(sample_normal.T.to_string())

