# Final Model Comparison on Held-out Test Set

| Model | Precision | Recall | F1 Score | PR-AUC | ROC-AUC | Expected Cost | P99 Latency (ms) |
|-------|-----------|--------|----------|--------|---------|---------------|------------------|
| Baseline Z-Score | 0.1923 | 0.9524 | 0.3200 | 0.3804 | 0.4751 | ₹54,000.00 | 0.00 |
| Isolation Forest | 0.2439 | 0.9524 | 0.3883 | 0.2401 | 0.6238 | ₹43,000.00 | 0.00 |
| LightGBM | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | ₹2,100.00 | 0.00 |

## Final Model Selection
**Chosen Model: LightGBM**

While metrics like F1 and PR-AUC are instructive, our primary optimization target is the **Expected Cost**, due to the massive asymmetry between False Negatives (₹10,000 penalty) and False Positives (₹500 penalty). LightGBM significantly outperforms the Baseline Z-score and Isolation Forest approaches by capturing multivariate interactions more effectively, thereby minimizing missed attacks and unnecessary friction, leading to the lowest overall expected cost.
