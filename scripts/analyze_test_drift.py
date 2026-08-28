import pandas as pd
import json

from src.models.lightgbm_detector import LightGBMDetector
detector = LightGBMDetector.load("data/processed/lightgbm.pkl")
test = pd.read_csv("data/processed/test/window_features_v1.csv")

scores = detector.predict_scores(test)
with open("data/processed/optimal_threshold.json") as f:
    thresh = json.load(f)["isolation_forest_threshold"]

preds = scores > thresh
test['pred'] = preds
test['score'] = scores

normals = test[test['is_synthetic_spike'] == False]
spikes = test[test['is_synthetic_spike'] == True]

print("Normal scores:", normals['score'].describe())
print("Spike scores:", spikes['score'].describe())

print("Threshold:", thresh)
