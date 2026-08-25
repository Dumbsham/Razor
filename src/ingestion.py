"""Load, validate, normalize, and chronologically split the PaySim transaction stream."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

# iss project ke kaam karne ke liye inn columns ka hona zaruri hai
REQUIRED_SOURCE_COLUMNS: Final[set[str]] = {
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
    "isFlaggedFraud",
}

CANONICAL_COLUMNS: Final[list[str]] = [
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
]

#renaming columns -> i.e. canonical schema
RENAME_MAP: Final[dict[str, str]] = {
    "step": "event_time",
    "type": "transaction_type",
    "nameOrig": "origin_account",
    "oldbalanceOrg": "origin_balance_before",
    "newbalanceOrig": "origin_balance_after",
    "nameDest": "destination_account",
    "oldbalanceDest": "destination_balance_before",
    "newbalanceDest": "destination_balance_after",
    "isFraud": "is_fraud",
}

#datatype of each column
READ_DTYPES: Final[dict[str, str]] = {
    "step": "int16",
    "type": "string",
    "amount": "float64",
    "nameOrig": "string",
    "oldbalanceOrg": "float64",
    "newbalanceOrig": "float64",
    "nameDest": "string",
    "oldbalanceDest": "float64",
    "newbalanceDest": "float64",
    "isFraud": "int8",
    "isFlaggedFraud": "int8",
}


@dataclass(frozen=True)
class TimeSplit:
    """Inclusive PaySim step boundaries for one chronological partition."""

    name: str
    start_step: int
    end_step: int


TIME_SPLITS: Final[tuple[TimeSplit, ...]] = (
    TimeSplit("train", 1, 520),
    TimeSplit("validation", 521, 631),
    TimeSplit("test", 632, 743),
)


def validate_source_columns(columns: set[str] | pd.Index) -> None:
    """Raise a clear error when a PaySim input is missing a required column."""
    missing_columns = REQUIRED_SOURCE_COLUMNS.difference(columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"PaySim input is missing required column(s): {missing}")


def load_transactions(csv_path: str | Path) -> pd.DataFrame:
    """Read PaySim, produce the canonical schema, and preserve chronological order."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"PaySim CSV not found: {path}")

    source_columns = pd.read_csv(path, nrows=0).columns
    validate_source_columns(source_columns)

    source = pd.read_csv(path, dtype=READ_DTYPES)
    transactions = source.rename(columns=RENAME_MAP)[CANONICAL_COLUMNS].copy()
    transactions.sort_values("event_time", kind="stable", inplace=True, ignore_index=True)
    return transactions


def split_transactions(transactions: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return the locked, non-overlapping chronological train/validation/test partitions."""
    if "event_time" not in transactions.columns:
        raise ValueError("Canonical transactions must include an 'event_time' column")

    splits: dict[str, pd.DataFrame] = {}
    for split in TIME_SPLITS:
        partition = transactions.loc[
            transactions["event_time"].between(split.start_step, split.end_step)
        ].copy()
        splits[split.name] = partition

    assigned_rows = sum(len(partition) for partition in splits.values())
    if assigned_rows != len(transactions):
        raise ValueError(
            "Transactions fall outside the locked time split boundaries; "
            f"assigned {assigned_rows:,} of {len(transactions):,} rows."
        )
    return splits


def build_split_summary(splits: dict[str, pd.DataFrame]) -> dict[str, object]:
    """Build a JSON-serializable summary used for reproducibility checks and reports."""
    split_summaries: dict[str, dict[str, int | float]] = {}
    for split in TIME_SPLITS:
        partition = splits[split.name]
        row_count = len(partition)
        fraud_count = int(partition["is_fraud"].sum())
        split_summaries[split.name] = {
            "start_step": split.start_step,
            "end_step": split.end_step,
            "row_count": row_count,
            "fraud_count": fraud_count,
            "fraud_rate": fraud_count / row_count if row_count else 0.0,
        }

    return {
        "schema_version": 1,
        "source": "Paysim.csv",
        "canonical_columns": CANONICAL_COLUMNS,
        "splits": split_summaries,
    }


def write_split_summary(summary: dict[str, object], output_path: str | Path) -> Path:
    """Write the reproducibility summary without persisting duplicate raw data."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return path
