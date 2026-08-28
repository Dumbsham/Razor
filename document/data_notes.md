# Data Notes

## Primary dataset

- File: `Paysim.csv` (repository root)
- SHA-256: `16910f90577b0d981bf8ff289714510bb89bc71bff7d3f220f024e287e4eea6b`
- Intended role: the sole source dataset for chronological replay, model development, and offline evaluation.
- Format: CSV, 6,362,620 transaction rows, 11 columns, no missing values.

## Observed schema

| Source field | Internal role | Notes |
|---|---|---|
| `step` | `event_time` | Integer simulation step; range 1–743. Treat as the replay clock. |
| `type` | `transaction_type` | `CASH_IN`, `CASH_OUT`, `DEBIT`, `PAYMENT`, or `TRANSFER`. |
| `amount` | `amount` | Range: 0 to 92,445,516.64; mean: 179,861.90. |
| `nameOrig` | `origin_account` | Source-side account identifier. |
| `nameDest` | `destination_account` | Destination/merchant proxy account identifier. |
| `oldbalanceOrg`, `newbalanceOrig` | origin balance features | Candidate backward-looking / consistency features. |
| `oldbalanceDest`, `newbalanceDest` | destination balance features | Candidate backward-looking / consistency features. |
| `isFraud` | offline label only | 8,213 positive labels (0.1291%). Never use as a training feature. |
| `isFlaggedFraud` | excluded field | Only 16 positives (0.000251%); do not model with it. |

## Distribution snapshot

| Transaction type | Rows |
|---|---:|
| `CASH_OUT` | 2,237,500 |
| `PAYMENT` | 2,151,495 |
| `CASH_IN` | 1,399,284 |
| `TRANSFER` | 532,909 |
| `DEBIT` | 41,432 |

## Chronological split (locked)

| Split | PaySim steps | Rows | `isFraud` positives | Fraud rate |
|---|---:|---:|---:|---:|
| Train | 1–520 | 6,082,007 | 5,781 | 0.0951% |
| Validation | 521–631 | 191,147 | 1,180 | 0.6173% |
| Held-out test | 632–743 | 89,466 | 1,252 | 1.3994% |

The test split must not be used for fitting, scaling, model selection, feature selection, threshold selection, or cost-assumption tuning before final evaluation.

## Data-quality observations and limitations

- The CSV is complete: no null values were found in any of the 11 columns.
- Fraud prevalence increases materially across later steps. This temporal shift is realistic enough to be worth reporting, but it means a time-based test is harder and should not be compared directly with random-split results.
- PaySim is simulated mobile-money data, not a live Razorpay merchant stream. Cost numbers and production-performance claims must remain illustrative.
- The data has no true IP address, device identifier, card BIN, geography, customer identity, merchant category, or chargeback outcome. `nameDest` is only a destination-account proxy, not a verified merchant identity.
- Most origin accounts are unique within each split, so repeated-origin velocity features should be validated before being relied upon. Prefer aggregate/window, destination-proxy, type, amount, and balance-pattern features where evidence supports them.
- Synthetic spike labels will be generated offline for spike-level evaluation and never exposed as an interactive attack or evasion tool.

## Source and license

- Declared upstream dataset: Kaggle, [Synthetic Financial Datasets For Fraud Detection — PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1), **Version 2**.
- Declared upstream file: `PS_20174392719_1491204439457_log.csv` (493.53 MB). The supplied local `Paysim.csv` matches this file's 6,362,620-row / 11-column schema and archive filename; its exact local contents are pinned by the SHA-256 above.
- License shown by the upstream Kaggle dataset: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Preserve required attribution and share-alike obligations in any published derivative artifact.
- Dataset reference: Lopez-Rojas, E., Elmir, A., & Axelsson, S. (2016), [*PaySim: A Financial Mobile Money Simulator for Fraud Detection*](https://www.msc-les.org/proceedings/emss/2016/EMSS2016_249.pdf), EMSS 2016, pp. 249–255.
