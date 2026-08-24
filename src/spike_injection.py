"""Offline-only deterministic fixtures for evaluating fraud-spike detection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCENARIO_SEED: Final = 20260823
ScenarioFamily = Literal["velocity_burst", "amount_repetition", "destination_concentration"]


@dataclass(frozen=True)
class SpikeScenario:
    """A safe evaluation fixture, defined only by aggregate behavioral characteristics."""

    scenario_id: str
    split: Literal["validation", "test"]
    family: ScenarioFamily
    start_step: int
    end_step: int
    injected_event_count: int


DEFAULT_SCENARIOS: Final[tuple[SpikeScenario, ...]] = (
    SpikeScenario("validation_velocity_01", "validation", "velocity_burst", 545, 546, 120),
    SpikeScenario("validation_amount_01", "validation", "amount_repetition", 590, 591, 100),
    SpikeScenario("test_velocity_01", "test", "velocity_burst", 655, 656, 120),
    SpikeScenario("test_amount_01", "test", "amount_repetition", 685, 686, 100),
    SpikeScenario("test_destination_01", "test", "destination_concentration", 715, 716, 100),
)

_REQUIRED_COLUMNS: Final[set[str]] = {
    "event_time",
    "transaction_type",
    "amount",
    "origin_account",
    "origin_balance_before",
    "origin_balance_after",
    "destination_account",
    "destination_balance_before",
    "destination_balance_after",
    "is_fraud",
}


def _validate_input(transactions: pd.DataFrame, scenarios: tuple[SpikeScenario, ...]) -> None:
    missing_columns = _REQUIRED_COLUMNS.difference(transactions.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Transactions are missing required canonical column(s): {missing}")

    if transactions.empty:
        raise ValueError("Cannot inject scenarios into an empty transaction stream")

    observed_steps = set(transactions["event_time"].unique())
    for scenario in scenarios:
        required_steps = set(range(scenario.start_step, scenario.end_step + 1))
        if not required_steps.issubset(observed_steps):
            raise ValueError(f"Scenario {scenario.scenario_id} falls outside the supplied transaction stream")


def _synthetic_rows(
    transactions: pd.DataFrame, scenario: SpikeScenario, rng: np.random.Generator
) -> pd.DataFrame:
    """Create clearly tagged synthetic rows without copying real account identifiers."""
    templates = transactions.sample(n=scenario.injected_event_count, replace=True, random_state=rng)
    events = pd.DataFrame(index=range(scenario.injected_event_count))
    events["event_time"] = rng.integers(scenario.start_step, scenario.end_step + 1, len(events))
    events["transaction_type"] = templates["transaction_type"].to_numpy()

    sampled_amounts = templates["amount"].to_numpy(dtype=float)
    if scenario.family == "amount_repetition":
        sampled_amounts = np.full(len(events), float(np.median(sampled_amounts)))
    events["amount"] = sampled_amounts

    event_number = np.arange(len(events))
    events["origin_account"] = [f"SYNTH_ORIGIN_{scenario.scenario_id}_{n}" for n in event_number]
    if scenario.family == "destination_concentration":
        events["destination_account"] = f"SYNTH_DEST_{scenario.scenario_id}"
    else:
        events["destination_account"] = [
            f"SYNTH_DEST_{scenario.scenario_id}_{n}" for n in event_number
        ]

    events["origin_balance_before"] = events["amount"]
    events["origin_balance_after"] = 0.0
    events["destination_balance_before"] = 0.0
    events["destination_balance_after"] = events["amount"]
    events["is_fraud"] = 0
    events["is_synthetic_spike_event"] = True
    events["synthetic_scenario_id"] = scenario.scenario_id
    return events


def build_step_labels(scenarios: tuple[SpikeScenario, ...]) -> pd.DataFrame:
    """Return one positive spike label for every affected PaySim time step."""
    records = []
    for scenario in scenarios:
        for event_time in range(scenario.start_step, scenario.end_step + 1):
            records.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "split": scenario.split,
                    "family": scenario.family,
                    "event_time": event_time,
                    "is_synthetic_spike": True,
                }
            )
    return pd.DataFrame.from_records(records).sort_values(
        ["event_time", "scenario_id"], ignore_index=True
    )


def inject_scenarios(
    transactions: pd.DataFrame,
    scenarios: tuple[SpikeScenario, ...] = DEFAULT_SCENARIOS,
    seed: int = SCENARIO_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Append deterministic, labeled fixtures and return the augmented stream plus step labels."""
    _validate_input(transactions, scenarios)
    rng = np.random.default_rng(seed)
    base = transactions.copy()
    base["is_synthetic_spike_event"] = False
    base["synthetic_scenario_id"] = pd.NA

    synthetic_events = [_synthetic_rows(base, scenario, rng) for scenario in scenarios]
    augmented = pd.concat([base, *synthetic_events], ignore_index=True)
    augmented.sort_values("event_time", kind="stable", inplace=True, ignore_index=True)
    return augmented, build_step_labels(scenarios)


def write_scenario_artifacts(
    transactions: pd.DataFrame,
    scenarios: tuple[SpikeScenario, ...],
    labels: pd.DataFrame,
    output_dir: str | Path,
    plot_path: str | Path,
) -> None:
    """Save small metadata artifacts and a timeline; never persist an attack-control interface."""
    artifact_dir = Path(output_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "scenario_manifest.json").write_text(
        json.dumps(
            {
                "seed": SCENARIO_SEED,
                "purpose": "offline-only evaluation fixtures for defensive spike detection",
                "scenarios": [asdict(scenario) for scenario in scenarios],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    labels.to_csv(artifact_dir / "spike_step_labels.csv", index=False)

    timeline = (
        transactions.groupby(["event_time", "is_synthetic_spike_event"], observed=True)
        .size()
        .unstack(fill_value=0)
        .rename(columns={False: "normal_events", True: "synthetic_events"})
    )
    timeline["total_events"] = timeline.sum(axis=1)
    timeline.to_csv(artifact_dir / "spike_timeline.csv")

    fig, (volume_axis, fixture_axis) = plt.subplots(
        2, 1, figsize=(12, 7), sharex=True, height_ratios=(3, 1)
    )
    volume_axis.plot(
        timeline.index, timeline["normal_events"], label="Base transactions", color="#6b7280"
    )
    volume_axis.plot(
        timeline.index, timeline["total_events"], label="With evaluation fixtures", color="#2563eb"
    )
    fixture_axis.bar(
        timeline.index,
        timeline["synthetic_events"],
        color="#2563eb",
        label="Injected evaluation events",
    )
    for scenario in scenarios:
        volume_axis.axvspan(scenario.start_step, scenario.end_step, color="#ef4444", alpha=0.16)
        fixture_axis.axvspan(scenario.start_step, scenario.end_step, color="#ef4444", alpha=0.16)
    volume_axis.set(title="Validation and Test Streams with Labeled Synthetic Spike Windows", ylabel="Transactions")
    fixture_axis.set(xlabel="PaySim step", ylabel="Fixture\nevents")
    volume_axis.legend()
    fixture_axis.legend(loc="upper right")
    fig.tight_layout()
    destination = Path(plot_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=160)
    plt.close(fig)
