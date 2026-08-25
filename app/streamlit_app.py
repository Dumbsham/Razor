import streamlit as st
import pandas as pd
import json
from pathlib import Path
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.isolation_forest import IsolationForestModel
from src.explain import explain_alert

st.set_page_config(page_title="Risk Monitoring Dashboard", layout="wide")
st.title("PaySim Risk Monitoring Dashboard")

@st.cache_data
def load_data():
    base_dir = Path(__file__).parent.parent
    
    # Load test data
    test_file = base_dir / "data" / "processed" / "test" / "window_features_v1.csv"
    if not test_file.exists():
        st.error("Test data not found. Please run the data pipelines first.")
        return None, None, None, None, None, None
    test_df = pd.read_csv(test_file).fillna(0)
    
    # Load model and threshold
    model_path = base_dir / "data" / "processed" / "isolation_forest.pkl"
    thresh_path = base_dir / "data" / "processed" / "optimal_threshold.json"
    
    if not model_path.exists() or not thresh_path.exists():
        st.error("Model or threshold not found. Run model training and validation.")
        return test_df, None, None, None, None, None
        
    iso_forest = IsolationForestModel.load(model_path)
    with open(thresh_path) as f:
        opt_thresh = json.load(f)["isolation_forest_threshold"]
        
    # Generate scores
    test_df['score'] = iso_forest.predict_scores(test_df)
    test_df['is_alert'] = test_df['score'] > opt_thresh
    
    # Load baseline stats for explainability
    stats_path = base_dir / "data" / "processed" / "baseline_zscore.json"
    with open(stats_path) as f:
        stats = json.load(f)
    train_means = stats["means"]
    train_stds = stats["stds"]
    
    # Load metrics reports
    metrics_path = base_dir / "reports" / "test_evaluation_report.json"
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)
            
    return test_df, iso_forest, opt_thresh, train_means, train_stds, metrics

test_df, iso_forest, opt_thresh, train_means, train_stds, metrics = load_data()

if test_df is not None and iso_forest is not None:
    tab1, tab2 = st.tabs(["🔴 Live Alerts Stream", "📊 Impact & Metrics"])
    
    with tab1:
        st.header("Stream Replay")
        
        # Determine the scenario bounds
        start_step = int(test_df['window_start'].min())
        end_step = int(test_df['window_start'].max())
        
        # Select the subset of data that actually has the demo scenario if possible, or just the whole test set
        # The demo scenario is around step 655
        current_step = st.slider("Current Time Step", min_value=start_step, max_value=end_step, value=start_step)
        
        # Display data up to current step
        historical_df = test_df[test_df['window_start'] <= current_step]
        current_window = test_df[test_df['window_start'] == current_step]
        
        st.subheader("Active Alerts")
        
        # Find recent alerts
        recent_alerts = historical_df[historical_df['is_alert'] == True].tail(5)
        
        if recent_alerts.empty:
            st.success("No active anomalies detected recently.")
        else:
            for idx, row in recent_alerts.iterrows():
                with st.container():
                    st.error(f"🚨 **ALERT FLAG** at Time Step {int(row['window_start'])}")
                    st.write(f"**Anomaly Score:** {row['score']:.4f} (Threshold: {opt_thresh:.4f})")
                    
                    # Explainability
                    reasons = explain_alert(row, train_means, train_stds)
                    if reasons:
                        st.write("**Primary Risk Factors:**")
                        for r in reasons:
                            st.write(f"- {r['signal']} ({r['contribution_level']} impact)")
                    
                    # Latency callout
                    if row['is_synthetic_spike']:
                        st.write("*(True Positive - Synthetic Spike Confirmed)*")
                    st.markdown("---")
        
        # Line chart for score over time
        st.line_chart(historical_df.set_index('window_start')['score'])

    with tab2:
        st.header("Evaluation Metrics (Held-out Test)")
        if metrics and "metrics" in metrics:
            col1, col2, col3 = st.columns(3)
            col1.metric("Precision", f"{metrics['metrics'].get('precision', 0):.4f}")
            col2.metric("Recall", f"{metrics['metrics'].get('recall', 0):.4f}")
            col3.metric("F1 Score", f"{metrics['metrics'].get('f1', 0):.4f}")
            
            st.subheader("Expected Cost")
            total_cost = metrics['metrics'].get('total_cost', 0)
            st.metric("Total Expected Cost", f"₹{total_cost:,.2f}")
            st.caption("Assumes Cost(FP) = ₹500, Cost(FN) = ₹10,000, Cost(TP) = ₹100")
            
            # Display charts if they exist
            base_dir = Path(__file__).parent.parent
            pr_curve_path = base_dir / "reports" / "validation_pr_curve.png"
            cost_curve_path = base_dir / "reports" / "validation_cost_vs_threshold.png"
            
            col_a, col_b = st.columns(2)
            with col_a:
                if pr_curve_path.exists():
                    st.image(str(pr_curve_path), caption="PR-AUC Curve (Validation)")
            with col_b:
                if cost_curve_path.exists():
                    st.image(str(cost_curve_path), caption="Expected Cost vs. Threshold (Validation)")
                    st.caption("**Note**: The cost parameters are illustrative for demonstration purposes.")
                    
        else:
            st.info("Metrics report not found. Run the test evaluation script to generate it.")
