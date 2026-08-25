import json
from pathlib import Path

def main():
    scenario = {
        "scenario_id": "test_velocity_01",
        "split": "test",
        "family": "velocity_burst",
        "start_step": 655,
        "end_step": 656,
        "injected_event_count": 120,
        "description": "A rapid burst of transactions indicating a velocity attack."
    }
    
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "demo_scenario.json", "w") as f:
        json.dump(scenario, f, indent=2)
        
    print("Demo scenario frozen.")

if __name__ == "__main__":
    main()
