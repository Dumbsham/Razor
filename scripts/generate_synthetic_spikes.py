"""Generate deterministic, offline-only synthetic-spike labels and a timeline artifact."""

from __future__ import annotations

import pandas as pd

from src.ingestion import load_transactions, split_transactions
from src.spike_injection import DEFAULT_SCENARIOS, inject_scenarios, write_scenario_artifacts


def main() -> None:
    transactions = load_transactions("Paysim.csv")
    augmented, labels = inject_scenarios(transactions)
    write_scenario_artifacts(
        augmented,
        DEFAULT_SCENARIOS,
        labels,
        output_dir="data/synthetic_spikes",
        plot_path="reports/synthetic_spike_timeline.png",
    )
    print(f"Generated {len(DEFAULT_SCENARIOS)} deterministic scenarios and {len(labels)} positive step labels")
    print("Artifacts: data/synthetic_spikes/ and reports/synthetic_spike_timeline.png")


if __name__ == "__main__":
    main()
