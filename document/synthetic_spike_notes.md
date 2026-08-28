# Synthetic Spike Evaluation Notes

## Purpose

PaySim contains transaction-level `isFraud` labels but no native labels for coordinated, time-windowed fraud spikes. We therefore use small, deterministic synthetic fixtures **only** to evaluate spike detection latency and window-level precision/recall. They are not presented as real incidents or exposed as a user-facing simulation tool.

## Scenario design

Five fixtures are injected only into validation and held-out test streams. Training data remains unchanged.

| Family | Behavioral signal represented | Instances |
|---|---|---:|
| Velocity burst | Abrupt increase in transactions during a short time interval | 2 |
| Amount repetition | Unusually repetitive transaction amounts during a short interval | 2 |
| Destination concentration | Many transactions directed toward one synthetic destination proxy | 1 |

The fixtures span two adjacent PaySim steps each. Each generated record is explicitly marked `is_synthetic_spike_event = True` in memory. Original PaySim account identifiers are not copied into the synthetic records.

## Labels and reproducibility

- Fixed seed: `20260823`
- Positive label unit: each affected PaySim step (`is_synthetic_spike = True`)
- Scenario metadata: `data/synthetic_spikes/scenario_manifest.json`
- Step labels: `data/synthetic_spikes/spike_step_labels.csv`
- Timeline data: `data/synthetic_spikes/spike_timeline.csv`
- Timeline chart: `reports/synthetic_spike_timeline.png`

Day 3 will choose the scoring-window size and convert these step labels to window labels. A scoring window is positive if it overlaps an affected labeled step; this mapping will be tested for leakage and documented when implemented.

## Guardrails and limitations

- These fixtures are deliberately simple, interpretable test cases—not a claim of real-world fraud behavior.
- Model settings and thresholds may be selected using validation fixtures only. Test fixtures remain held out until final evaluation.
- The injection generator is offline-only and is never wired to Streamlit or exposed as an interactive control.
