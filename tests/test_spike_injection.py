import pandas as pd
from pandas.testing import assert_frame_equal

from src.spike_injection import SpikeScenario, build_step_labels, inject_scenarios


def _transactions() -> pd.DataFrame:
    rows = []
    for step in range(10, 14):
        for number in range(3):
            rows.append(
                {
                    "event_time": step,
                    "transaction_type": "TRANSFER",
                    "amount": 100.0 + number,
                    "origin_account": f"C{step}_{number}",
                    "origin_balance_before": 200.0,
                    "origin_balance_after": 100.0,
                    "destination_account": f"M{step}_{number}",
                    "destination_balance_before": 0.0,
                    "destination_balance_after": 100.0,
                    "is_fraud": 0,
                }
            )
    return pd.DataFrame(rows)


def test_injection_is_deterministic_and_preserves_base_rows():
    scenario = SpikeScenario("test_fixture", "test", "amount_repetition", 11, 12, 6)

    first_stream, first_labels = inject_scenarios(_transactions(), (scenario,), seed=7)
    second_stream, second_labels = inject_scenarios(_transactions(), (scenario,), seed=7)

    assert_frame_equal(first_stream, second_stream)
    assert_frame_equal(first_labels, second_labels)
    assert len(first_stream) == 18
    assert first_stream["is_synthetic_spike_event"].sum() == 6
    assert first_stream.loc[first_stream["is_synthetic_spike_event"], "amount"].nunique() == 1


def test_step_labels_cover_every_affected_step():
    scenario = SpikeScenario("validation_fixture", "validation", "velocity_burst", 10, 12, 6)

    labels = build_step_labels((scenario,))

    assert labels["event_time"].tolist() == [10, 11, 12]
    assert labels["is_synthetic_spike"].all()
