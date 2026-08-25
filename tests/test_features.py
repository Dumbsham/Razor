import pandas as pd
import pytest

from src.features import build_window_features, assert_no_future_events

def test_window_features_no_future_data_leakage():
    # Construct dummy transaction stream
    tx = pd.DataFrame({
        "event_time": [1, 2, 3, 4, 5],
        "amount": [10.0, 20.0, 30.0, 40.0, 50.0],
        "origin_account": ["A", "B", "A", "C", "B"],
        "destination_account": ["X", "Y", "X", "Z", "Y"]
    })
    
    features = build_window_features(tx, lookback_steps=3, stride_steps=1)
    
    # Verify bounds
    assert_no_future_events(features, tx)
    # The first window starts at min_step + lookback = 1 + 3 = 4
    # The history for window_start=4 must be steps 1, 2, 3
    assert not features.empty
    row_t4 = features[features["window_start"] == 4].iloc[0]
    assert row_t4["event_count"] == 3
    assert row_t4["amount_mean"] == 20.0  # (10 + 20 + 30) / 3

def test_features_handle_missing_columns():
    tx = pd.DataFrame({
        "event_time": [1, 2],
        "amount": [10.0, 20.0],
        # Missing origin_account, destination_account
    })
    
    with pytest.raises(ValueError, match="Transactions are missing required column\\(s\\)"):
        build_window_features(tx, lookback_steps=3, stride_steps=1)

def test_empty_dataframe():
    tx = pd.DataFrame(columns=["event_time", "amount", "origin_account", "destination_account"])
    features = build_window_features(tx, lookback_steps=3, stride_steps=1)
    assert features.empty

def test_step_labels_applied_correctly():
    tx = pd.DataFrame({
        "event_time": [1, 2, 3, 4, 5, 6],
        "amount": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "origin_account": ["A", "B", "C", "D", "E", "F"],
        "destination_account": ["X", "Y", "Z", "W", "V", "U"]
    })
    
    # Label a spike at step 5
    step_labels = pd.DataFrame({
        "event_time": [5],
        "is_synthetic_spike": [True],
        "scenario_id": ["spike_1"]
    })
    
    features = build_window_features(tx, lookback_steps=2, stride_steps=1, step_labels=step_labels)
    # Windows:
    # start 3: history 1, 2. (Window 3 to 4)
    # start 4: history 2, 3. (Window 4 to 5) -> intersects step 5? window_end for start=4 is 4+2-1=5
    # start 5: history 3, 4. (Window 5 to 6) -> intersects step 5? yes, window_start=5
    # start 6: history 4, 5. (Window 6 to 7) -> intersects step 5? no, window_start=6
    
    # window_start=4 -> window_end=5
    row_4 = features[features["window_start"] == 4].iloc[0]
    assert row_4["is_synthetic_spike"] == True
    assert row_4["scenario_ids"] == "spike_1"
    
    # window_start=3 -> window_end=4
    row_3 = features[features["window_start"] == 3].iloc[0]
    assert row_3["is_synthetic_spike"] == False
    assert row_3["scenario_ids"] == ""
