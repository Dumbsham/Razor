import sys
import pandas as pd
import numpy as np
from src.ingestion import load_transactions
from src.spike_injection import inject_scenarios, get_scenarios
from src.features import build_window_features

def main():
    transactions = load_transactions("Paysim.csv")
    
    print("--- 1. Checking Actual Injected Event Counts ---")
    difficulties = ["easy", "medium", "hard"]
    for diff in difficulties:
        scenarios = get_scenarios(diff)
        aug, _ = inject_scenarios(transactions, scenarios, strict_isolation=False)
        test_aug = aug[aug["event_time"] > 600]
        actual_injected = test_aug["is_synthetic_spike_event"].sum()
        print(f"Difficulty '{diff}': {actual_injected} total injected events in Test split")

    print("\n--- 2. Comparing Feature Values (Easy vs Hard) ---")
    # Easy
    easy_scenarios = get_scenarios("easy")
    easy_aug, easy_labels = inject_scenarios(transactions, easy_scenarios, strict_isolation=False)
    easy_test = easy_aug[easy_aug["event_time"] > 600]
    easy_feat = build_window_features(easy_test, step_labels=easy_labels).fillna(0)
    
    # Hard
    hard_scenarios = get_scenarios("hard")
    hard_aug, hard_labels = inject_scenarios(transactions, hard_scenarios, strict_isolation=False)
    hard_test = hard_aug[hard_aug["event_time"] > 600]
    hard_feat = build_window_features(hard_test, step_labels=hard_labels).fillna(0)
    
    easy_spikes = easy_feat[easy_feat["is_synthetic_spike"] == True]
    hard_spikes = hard_feat[hard_feat["is_synthetic_spike"] == True]
    
    print("Average max_entity_relative_velocity on Positive Test Windows:")
    print(f"Easy: {easy_spikes['max_entity_relative_velocity'].mean():.2f}")
    print(f"Hard: {hard_spikes['max_entity_relative_velocity'].mean():.2f}")
    
    print("\n--- 4. Raw Transaction Data for a Hard Spike ---")
    # Show the injected events for the first hard test scenario (test_velocity_01, step 655-656)
    hard_target_events = hard_test[
        (hard_test["event_time"].between(655, 656)) & 
        (hard_test["is_synthetic_spike_event"] == True)
    ]
    print(f"Found {len(hard_target_events)} events for 'test_velocity_01' (expected 25)")
    print(hard_target_events[["event_time", "amount", "origin_account", "destination_account", "is_synthetic_spike_event"]].head(10).to_string())
    print("... (showing first 10 events of the burst)")

if __name__ == "__main__":
    main()
