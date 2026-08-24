import pandas as pd
import pytest

from src.ingestion import (
    CANONICAL_COLUMNS,
    REQUIRED_SOURCE_COLUMNS,
    build_split_summary,
    load_transactions,
    split_transactions,
)


def _source_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "step": [632, 1, 521],
            "type": ["TRANSFER", "PAYMENT", "CASH_OUT"],
            "amount": [300.0, 100.0, 200.0],
            "nameOrig": ["C3", "C1", "C2"],
            "oldbalanceOrg": [300.0, 100.0, 200.0],
            "newbalanceOrig": [0.0, 0.0, 0.0],
            "nameDest": ["M3", "M1", "M2"],
            "oldbalanceDest": [0.0, 0.0, 0.0],
            "newbalanceDest": [300.0, 100.0, 200.0],
            "isFraud": [1, 0, 0],
            "isFlaggedFraud": [0, 0, 0],
        }
    )


def test_load_normalizes_and_sorts_transactions(tmp_path):
    source_path = tmp_path / "Paysim.csv"
    _source_frame().to_csv(source_path, index=False)

    transactions = load_transactions(source_path)

    assert transactions.columns.tolist() == CANONICAL_COLUMNS
    assert transactions["event_time"].tolist() == [1, 521, 632]
    assert "isFlaggedFraud" not in transactions.columns


def test_load_rejects_missing_required_source_columns(tmp_path):
    source_path = tmp_path / "Paysim.csv"
    incomplete = _source_frame().drop(columns="nameDest")
    incomplete.to_csv(source_path, index=False)

    with pytest.raises(ValueError, match="nameDest"):
        load_transactions(source_path)


def test_locked_splits_are_complete_non_overlapping_and_chronological(tmp_path):
    source_path = tmp_path / "Paysim.csv"
    _source_frame().to_csv(source_path, index=False)
    splits = split_transactions(load_transactions(source_path))

    assert set(splits) == {"train", "validation", "test"}
    assert sum(len(partition) for partition in splits.values()) == 3
    assert splits["train"]["event_time"].max() < splits["validation"]["event_time"].min()
    assert splits["validation"]["event_time"].max() < splits["test"]["event_time"].min()

    summary = build_split_summary(splits)
    assert summary["splits"]["test"]["fraud_count"] == 1


def test_required_schema_is_complete():
    assert len(REQUIRED_SOURCE_COLUMNS) == 11
