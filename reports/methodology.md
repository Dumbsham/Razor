# Methodology Note

## Time Splits
The dataset is strictly split chronologically into:
- **Train**: Used for baseline normalization, scaler fitting, and Isolation Forest training.
- **Validation**: Used for model tuning, threshold selection, and cost evaluation.
- **Test**: Strictly held-out. Never used for fitting or tuning. Evaluated only once.

## Synthetic Labels
Since public datasets lack dense, coordinated spike labels, we injected seeded synthetic spikes into the validation and test sets. These represent coordinated bursts of anomalous transactions. The labels are generated purely deterministically.

## Assumptions
- **Cost Assumptions**:
  - False Positive (FP) Cost: ₹500 (review time and potential customer friction).
  - False Negative (FN) Cost: ₹10,000 (expected loss from a missed fraudulent burst).
  - True Positive (TP) Cost: ₹100 (standard operational review cost).
- **Threshold Selection**: We optimized the threshold to minimize the expected total business cost on the validation set, rather than optimizing for raw accuracy or F1 score.

## Limitations
- Synthetic labels do not perfectly capture the evolving nature of real-world fraud tactics.
- The model uses static historical features which might drift over time in a live environment.
