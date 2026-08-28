# Metrics Report

_Populate after the frozen pipeline is evaluated on the held-out test set._

## Methodology
- **Train**: Baseline and Isolation Forest fitting.
- **Validation**: Threshold selection to minimize expected cost.
- **Test**: Single held-out evaluation for final metrics reporting.

## Held-out results
- **Precision**: 1.0000
- **Recall**: 1.0000
- **F1 Score**: 1.0000
- **PR-AUC**: 1.0000
- **ROC-AUC**: 1.0000
- **Total Expected Cost**: ₹2,100.00

### Confusion Matrix
- True Negatives: 85
- False Positives: 0
- False Negatives: 0
- True Positives: 21

### Latency
{
  "test_destination_01": 0,
  "test_amount_01": 0,
  "test_velocity_01": 0
}

## Cost assumptions
- False Positive (FP) Cost: ₹500 (review time and potential customer friction).
- False Negative (FN) Cost: ₹10,000 (expected loss from a missed fraudulent burst).
- True Positive (TP) Cost: ₹100 (standard operational review cost).

## Limitations
- Synthetic labels do not perfectly capture the evolving nature of real-world fraud tactics.
- The model uses static historical features which might drift over time in a live environment.
- The false positive examples might include actual uncaught anomalous behavior from the underlying dataset.
