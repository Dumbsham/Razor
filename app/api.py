from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
from pathlib import Path
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.lightgbm_detector import LightGBMDetector
from src.explain import explain_alert

app = FastAPI(title="PaySim Risk API")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    test_df = None
    detector = None
    opt_thresh = 0.0
    train_means = {}
    train_stds = {}
    metrics = {}

state = AppState()

@app.on_event("startup")
def load_data():
    base_dir = Path(__file__).parent.parent
    
    # Load test data
    test_file = base_dir / "data" / "processed" / "test" / "window_features_v1.csv"
    if test_file.exists():
        state.test_df = pd.read_csv(test_file).fillna(0)
    
    # Load model and threshold
    model_path = base_dir / "data" / "processed" / "lightgbm.pkl"
    thresh_path = base_dir / "data" / "processed" / "optimal_threshold.json"
    
    if model_path.exists() and thresh_path.exists():
        state.detector = LightGBMDetector.load(model_path)
        with open(thresh_path) as f:
            state.opt_thresh = json.load(f)["isolation_forest_threshold"]
            
        if state.test_df is not None:
            state.test_df['score'] = state.detector.predict_scores(state.test_df)
            state.test_df['is_alert'] = state.test_df['score'] > state.opt_thresh
    
    # Load baseline stats for explainability
    stats_path = base_dir / "data" / "processed" / "baseline_zscore.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        state.train_means = stats.get("means", {})
        state.train_stds = stats.get("stds", {})
    
    # Fill missing means/stds using test_df to ensure explain_alert can check all features
    if state.test_df is not None:
        numeric_cols = state.test_df.select_dtypes(include=['number']).columns
        exclude_cols = {'window_start', 'window_end', 'feature_cutoff', 'lookback_start', 'score', 'is_alert'}
        for col in numeric_cols:
            if col not in state.train_means and col not in exclude_cols:
                state.train_means[col] = float(state.test_df[col].mean())
                std = float(state.test_df[col].std())
                state.train_stds[col] = std if std > 0 else 1.0
    
    # Load metrics reports
    metrics_path = base_dir / "reports" / "test_evaluation_report.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            state.metrics = json.load(f)

@app.get("/api/status")
def get_status():
    return {
        "status": "OPERATIONAL" if state.test_df is not None and state.detector is not None else "ERROR",
        "dataset": "PAYSIM-TEST",
        "model": "LightGBM",
        "threshold": state.opt_thresh,
        "total_windows": len(state.test_df) if state.test_df is not None else 0
    }

@app.get("/api/metrics")
def get_metrics():
    if not state.metrics:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return state.metrics

@app.get("/api/stream/info")
def get_stream_info():
    if state.test_df is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return {
        "start_step": int(state.test_df['window_start'].min()),
        "end_step": int(state.test_df['window_start'].max())
    }

@app.get("/api/stream/historical/{step}")
def get_historical_data(step: int):
    if state.test_df is None:
        raise HTTPException(status_code=404, detail="Data not found")
    
    hist_df = state.test_df[state.test_df['window_start'] <= step]
    
    # Return minimal data for the chart to keep payload small
    chart_data = hist_df[['window_start', 'score', 'is_alert']].to_dict(orient='records')
    
    # Get active alerts (last 10 alerts up to current step)
    alerts_df = hist_df[hist_df['is_alert'] == True].tail(10)
    
    alerts = []
    for _, row in alerts_df.iterrows():
        reasons = explain_alert(row, state.train_means, state.train_stds)
        alerts.append({
            "step": int(row['window_start']),
            "score": float(row['score']),
            "is_synthetic_spike": bool(row['is_synthetic_spike']),
            "reasons": reasons
        })
    alerts.reverse() # Most recent first
    
    return {
        "chart_data": chart_data,
        "alerts": alerts
    }
