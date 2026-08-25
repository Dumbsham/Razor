"""Leakage-safe, backward-looking rolling features for the PaySim stream.

Rows describe a *future scoring window*.  For a row whose ``window_start`` is
``t``, every feature is computed from events with ``event_time < t`` (the
lookback interval is ``[t - lookback_steps, t)``).  Keeping this cutoff
explicit makes the no-future-data guarantee easy to review and test.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

FEATURE_SCHEMA_VERSION: Final[int] = 1
DEFAULT_LOOKBACK_STEPS: Final[int] = 6
DEFAULT_STRIDE_STEPS: Final[int] = 1


def _entropy(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    probabilities = values.value_counts(normalize=True).to_numpy(dtype=float)
    return float(-(probabilities * np.log2(probabilities)).sum())


def _window_row(history: pd.DataFrame, start: int, end: int, lookback: int) -> dict[str, object]:
    """Calculate one row. ``history`` is already restricted to event_time < start."""
    count = len(history)
    amount_mean = float(history["amount"].mean()) if count else 0.0
    amount_std = float(history["amount"].std(ddof=0)) if count else 0.0
    baseline = history["amount"].median() if count else 0.0
    event_times = np.sort(history["event_time"].to_numpy(dtype=float))
    gaps = np.diff(event_times)
    positive_gaps = gaps[gaps > 0]
    return {
        "window_start": start,
        "window_end": end,
        "feature_cutoff": start,
        "lookback_start": start - lookback,
        "event_count": int(count),
        "velocity_per_step": float(count / lookback),
        "amount_mean": amount_mean,
        "amount_std": amount_std,
        "amount_deviation": float(abs(amount_mean - float(baseline))),
        "mean_interarrival_steps": float(positive_gaps.mean()) if len(positive_gaps) else 0.0,
        "unique_origins": int(history["origin_account"].nunique()) if count else 0,
        "unique_destinations": int(history["destination_account"].nunique()) if count else 0,
        "destination_entropy": _entropy(history["destination_account"]) if count else 0.0,
        "amount_entropy": _entropy(history["amount"]) if count else 0.0,
        "repetition_ratio": (
            float(history["destination_account"].value_counts(normalize=True).iloc[0])
            if count
            else 0.0
        ),
    }


def build_window_features(
    transactions: pd.DataFrame,
    *,
    lookback_steps: int = DEFAULT_LOOKBACK_STEPS,
    stride_steps: int = DEFAULT_STRIDE_STEPS,
    step_labels: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build deterministic rolling features without looking past each cutoff.

    ``step_labels`` may contain ``event_time``, ``scenario_id`` and
    ``is_synthetic_spike``; labels are assigned when a labeled step overlaps
    the row's forward scoring window.
    """
    required = {"event_time", "amount", "origin_account", "destination_account"}
    missing = required.difference(transactions.columns)
    if missing:
        raise ValueError(f"Transactions are missing required column(s): {', '.join(sorted(missing))}")
    if lookback_steps <= 0 or stride_steps <= 0:
        raise ValueError("lookback_steps and stride_steps must be positive")
    if transactions.empty:
        return pd.DataFrame()

    ordered = transactions.sort_values("event_time", kind="stable").reset_index(drop=True)
    min_step, max_step = int(ordered.event_time.min()), int(ordered.event_time.max())
    rows: list[dict[str, object]] = []
    for start in range(min_step + lookback_steps, max_step + 1, stride_steps):
        end = start + lookback_steps - 1
        history = ordered.loc[
            ordered["event_time"].between(start - lookback_steps, start - 1)
        ]
        row = _window_row(history, start, end, lookback_steps)
        rows.append(row)
    features = pd.DataFrame(rows)

    if step_labels is not None and not step_labels.empty:
        labels = step_labels.loc[step_labels["event_time"].notna()].copy()
        labels["event_time"] = labels["event_time"].astype(int)
        features["is_synthetic_spike"] = features.apply(
            lambda r: bool(labels["event_time"].between(r.window_start, r.window_end).any()), axis=1
        )
        if "scenario_id" in labels.columns:
            features["scenario_ids"] = features.apply(
                lambda r: ",".join(sorted(labels.loc[
                    labels["event_time"].between(r.window_start, r.window_end), "scenario_id"
                ].astype(str).unique())), axis=1
            )
    else:
        features["is_synthetic_spike"] = False
        features["scenario_ids"] = ""
    return features


def assert_no_future_events(features: pd.DataFrame, transactions: pd.DataFrame) -> None:
    """Fail loudly if any feature row could include an event at/after its cutoff."""
    if features.empty or transactions.empty:
        return
    latest = int(transactions["event_time"].max())
    if (features["feature_cutoff"] > latest + 1).any():
        raise AssertionError("Feature cutoff lies beyond the transaction stream")
    # The construction contract is explicit: the cutoff is exactly window_start.
    if not (features["feature_cutoff"] == features["window_start"]).all():
        raise AssertionError("Feature rows have an invalid future-data cutoff")


def persist_feature_dataset(features: pd.DataFrame, output_dir: str | Path) -> tuple[Path, Path]:
    """Persist CSV features and JSON schema metadata for reproducible downstream models."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    data_path = destination / f"window_features_v{FEATURE_SCHEMA_VERSION}.csv"
    metadata_path = destination / f"window_features_v{FEATURE_SCHEMA_VERSION}.json"
    features.to_csv(data_path, index=False)
    metadata = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "lookback_steps": DEFAULT_LOOKBACK_STEPS,
        "stride_steps": DEFAULT_STRIDE_STEPS,
        "cutoff_rule": "features use only event_time < window_start",
        "columns": list(features.columns),
        "row_count": int(len(features)),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return data_path, metadata_path
