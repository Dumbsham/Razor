# 10-Day Hackathon Demo Plan — Fraud-Spike Detector

**Time budget:** 6 hours/day × 10 days = **60 focused hours**  
**Win condition:** a credible, defense-only, end-to-end demo that replays a payment stream, detects coordinated fraud spikes quickly, explains alerts at an aggregate level, and proves the business trade-off with a held-out cost curve.

## Product thesis

Most fraud demos stop at a model score. This demo should answer the question a risk manager actually has: **“What is happening, how quickly did we catch it, why should I trust this alert, and what does the chosen operating point save?”**

The differentiators to emphasize to judges are:

- Streaming/windowed detection rather than isolated transaction classification.
- Strict time-based train/validation/test separation to avoid leakage.
- Threshold selection based on expected ₹ cost, not accuracy or F1 alone.
- A calm, interpretable dashboard designed for incident response.
- Defense-only design: no controls or details that help tune an attack or evade detection.

## Scope decisions — make these on Day 1

| Area | Commit to | Explicitly defer |
|---|---|---|
| Dataset | **PaySim** if available quickly; otherwise Kaggle ULB Credit Card Fraud. Pick one and do not switch after Day 1. | Combining datasets or building a production ingestion connector. |
| Detection | Rolling EWMA/z-score baseline + Isolation Forest on window-level features. | Autoencoder unless all Day 7 acceptance checks pass. |
| “Real time” | Deterministic replay of time-ordered transactions at adjustable demo speed. | Kafka, websockets, real payment integration. |
| Explainability | Safe, bucketed reasons such as “unusual velocity” and “repetitive pattern”; show relative contributions, not raw thresholds. | Raw rules, exact threshold values, or attack simulation controls. |
| UI | One Streamlit app with Replay, Alerts, and Impact views. | A multi-page production admin system, auth, or deployment complexity. |

## Definition of done

Before presentation day, all items below must be true.

- [ ] A fresh setup command runs the app and reproduces the reported metrics.
- [ ] One fixed, seeded demo scenario replays from normal traffic into a labeled spike.
- [ ] The app alerts during that spike and shows a clear detection-latency callout.
- [ ] Reported metrics come only from the untouched time-held-out test set.
- [ ] The dashboard includes PR-AUC, precision, recall, F1, confusion matrix, detection latency, and a cost-vs-threshold chart.
- [ ] The selected operating point is justified by minimum expected loss and its cost assumptions are visibly labeled illustrative.
- [ ] Every alert has 2–3 safe, human-readable contributing signals.
- [ ] No dashboard element exposes evasion-relevant raw thresholds, weights, synthetic-spike controls, or live attack construction.
- [ ] A judge can understand the value in 30 seconds and complete the full story in under 3 minutes.

## Daily execution plan

### Day 1 — Lock scope and establish a reproducible foundation (6h)

**Outcome:** a runnable repository, one selected dataset, and a written data contract.

- [x] **0:00–0:45:** Create the Python environment with `uv`, pin the minimal dependencies, and add a concise setup section to the README.
- [x] **0:45–2:00:** Obtain the chosen public dataset and record source, license/access notes, row count, fields, and known limitations in `reports/data_notes.md`.
- [x] **2:00–3:30:** Run compact EDA: timestamp coverage, amount distribution, missingness, entity identifiers available, class imbalance, and transaction volume by time bucket.
- [x] **3:30–4:30:** Define the canonical transaction schema used internally: event time, amount, entity key, merchant/destination key, and optional geography.
- [x] **4:30–5:30:** Implement `src/ingestion.py` to load, normalize, sort by time, and produce deterministic time splits.
- [x] **5:30–6:00:** Commit to train/validation/test date or row ranges and document them. Do not revisit after model work starts.

**Acceptance check:** running ingestion produces three chronological, non-overlapping datasets and a small summary table.

### Day 2 — Create trustworthy labeled spike scenarios (6h)

**Outcome:** deterministic synthetic labels for spike-level evaluation without contaminating training.

- [x] **0:00–1:00:** Define a spike label precisely: a contiguous time window with coordinated abnormal behavior, plus start/end time and entity group.
- [x] **1:00–3:00:** Implement a seeded, offline-only injection pipeline for validation and test portions. Keep source code inaccessible from the dashboard.
- [x] **3:00–4:00:** Create 3–5 scenario families with varied severity and timing; avoid a single easy-to-learn pattern.
- [x] **4:00–5:00:** Add labels at PaySim-step level; Day 3 will map them to scoring windows. No original transaction IDs are needed because injected records are new, explicitly tagged evaluation fixtures.
- [x] **5:00–6:00:** Visualize normal versus injected transaction volume and manually validate each scenario for plausibility.

**Acceptance check:** rerunning the same seed yields identical scenarios and labels; every test spike is visible in a simple time-series plot.

### Day 3 — Build leakage-safe rolling features (6h)

**Outcome:** a versioned window-feature table fit for both models.

- [x] **0:00–1:00:** Choose one window size and one stride that give a smooth demo while retaining enough observations; document the choice.
- [x] **1:00–3:30:** Implement backward-looking-only features: velocity/count, amount mean/std/deviation, inter-arrival time, unique destinations, and entropy/repetition signals where fields allow.
- [x] **3:30–4:30:** Ensure feature state uses only events before each scoring window; add an assertion/test guarding against future timestamps.
- [x] **4:30–5:15:** Persist a processed feature dataset with schema/version metadata.
- [x] **5:15–6:00:** Plot feature distributions for normal and labeled-spike windows as a sanity check.

**Acceptance check:** processed data is reproducible from raw data and a reviewer can verify no future events contribute to a row.

### Day 4 — Ship the explainable baseline (6h)

**Outcome:** an end-to-end baseline that detects some spikes and establishes a comparison point.

- [x] **0:00–2:00:** Implement rolling EWMA/z-score scoring in `src/models/baseline_zscore.py` using training-derived normalization.
- [x] **2:00–3:00:** Tune only on validation data, using a small documented search grid.
- [x] **3:00–4:30:** Implement window-to-spike alert grouping and detection-latency calculation.
- [x] **4:30–5:15:** Calculate validation precision, recall, F1, PR-AUC where applicable, confusion matrix, and latency.
- [x] **5:15–6:00:** Save a baseline report and identify the two strongest, safely phrased alert reasons.

**Acceptance check:** one command produces baseline metrics, an alert timeline, and a latency result for every labeled test scenario (even if missed).

### Day 5 — Train the primary Isolation Forest model (6h)

**Outcome:** a robust primary detector and a fair comparison to baseline.

- [x] **0:00–1:00:** Finalize feature set and preprocessing pipeline; fit scalers only on training windows.
- [x] **1:00–2:30:** Train Isolation Forest on normal/training windows and persist model plus feature schema.
- [x] **2:30–4:00:** Evaluate score behavior on validation windows; inspect false positives rather than tuning blindly.
- [x] **4:00–5:00:** Choose a validation threshold candidate using the business-cost objective.
- [x] **5:00–6:00:** Produce a baseline-vs-Isolation-Forest comparison table with consistent splits and definitions.

**Acceptance check:** the primary model improves at least one meaningful objective over baseline, or the baseline remains the documented production choice. Never hide an unfavorable comparison.

### Day 6 — Make the business case and freeze the model (6h)

**Outcome:** credible operating-point selection and a test plan that cannot drift.

- [x] **0:00–1:30:** Define transparent illustrative cost assumptions: review/customer-friction cost for a false positive; expected loss for a missed spike; review cost for a true positive.
- [x] **1:30–3:00:** Implement `src/evaluate.py` to calculate expected cost across validation thresholds.
- [x] **3:00–4:00:** Produce cost-vs-threshold, precision-recall, and confusion-matrix artifacts.
- [x] **4:00–4:45:** Select and freeze the operating point from validation minimum expected cost.
- [x] **4:45–5:30:** Write a short methodology note explaining time splits, synthetic labels, assumptions, and limitations.
- [x] **5:30–6:00:** Add a single `make`/`uv run` command or script that reproduces all offline artifacts.

**Acceptance check:** model, features, threshold, and cost assumptions are frozen before test evaluation; the methodology explains why cost optimization may choose a different threshold from max-F1.

### Day 7 — Run the one honest held-out evaluation (6h)

**Outcome:** final evidence for the demo.

- [x] **0:00–1:00:** Verify that test data has never been used for fitting, scaling, parameter selection, or threshold choice.
- [x] **1:00–2:30:** Run the frozen pipeline once on held-out test data and save immutable metric outputs.
- [x] **2:30–3:30:** Generate final PR-AUC, ROC-AUC if meaningful, precision, recall, F1, confusion matrix, detection latency, and cost curve.
- [x] **3:30–4:30:** Review false positives and false negatives; select one honest example of each for notes, not necessarily the live demo.
- [x] **4:30–5:15:** Create `reports/metrics_report.md` with assumptions, results, comparison table, and limitations.
- [x] **5:15–6:00:** Freeze one compelling seeded replay scenario for the demo; separate it from the final evaluation artifact if needed.

**Acceptance check:** every number shown to judges is traceable to a saved held-out report, and any synthetic-label limitation is clearly disclosed.

### Day 8 — Build the judge-friendly Streamlit experience (6h)

**Outcome:** a cohesive app, not a notebook collection.

- [ ] **0:00–1:00:** Sketch the single-page flow: status → replay timeline → alert detail → impact/metrics.
- [ ] **1:00–2:30:** Build the replay view with Start/Reset and a fixed safe speed selector; use the frozen scenario only.
- [ ] **2:30–3:30:** Add alert cards: time, severity label, detection latency, and 2–3 aggregate contributing signals.
- [ ] **3:30–4:30:** Add an impact view with held-out metrics, cost chart, and plain-language threshold rationale—without showing exact evasion-relevant values.
- [ ] **4:30–5:15:** Add an explicit “Defense-only design” note and a data/assumptions disclosure.
- [ ] **5:15–6:00:** Test fresh app startup, Reset, and the complete replay without manual file edits.

**Acceptance check:** a new viewer can use the app to see normal activity, alert emergence, explanation, and business impact in a single sitting.

### Day 9 — Harden the demo and improve the story (6h)

**Outcome:** reliable performance and presentation-ready assets.

- [ ] **0:00–1:00:** Test in a clean environment or from a fresh terminal; remove path-dependent and notebook-only assumptions.
- [ ] **1:00–2:00:** Test error states: missing data, missing model artifacts, and empty replay; provide clear recovery guidance.
- [ ] **2:00–3:00:** Optimize startup time and cache static processed/model artifacts.
- [ ] **3:00–4:00:** Capture polished screenshots/GIF or a short backup demo recording in case of environment failure.
- [ ] **4:00–5:00:** Draft a 5-slide deck: problem, product/replay, detection approach, proof & cost curve, responsible/defense-only close.
- [ ] **5:00–6:00:** Run the 3-minute script twice; log every confusing transition or slow interaction.

**Acceptance check:** the app starts reliably, the fallback recording exists, and the live path fits in three minutes with time for questions.

### Day 10 — Polish, rehearse, and submit (6h)

**Outcome:** a confident submission with no last-minute technical risk.

- [ ] **0:00–1:00:** Fix only defects found during rehearsal; do not add new ML approaches or features.
- [ ] **1:00–2:00:** Polish README: problem, architecture, quick start, dataset/source, results, screenshots, limitations, and defense-only statement.
- [ ] **2:00–3:00:** Rehearse the full pitch with timer: 30-second hook, 90-second product walkthrough, 45-second evidence, 15-second close.
- [ ] **3:00–4:00:** Prepare concise answers for data realism, synthetic labels, false positives, threshold choice, latency, scalability, and safety.
- [ ] **4:00–5:00:** Run final reproducibility test and verify all required links, screenshots, reports, and submission fields.
- [ ] **5:00–6:00:** Submit early; keep the final hour for a calm final run-through and backup verification.

**Acceptance check:** submission matches the working repository exactly and someone else can follow Quick Start without oral help.

## Recommended project milestones

| Milestone | Deadline | Evidence |
|---|---:|---|
| Data foundation | End of Day 1 | Chronological splits + data notes |
| Labeled evaluation stream | End of Day 2 | Seeded scenarios + timeline plot |
| Working baseline | End of Day 4 | Alert timeline + metrics script |
| Primary model and business objective | End of Day 6 | Validation cost curve + frozen config |
| Final evidence | End of Day 7 | Held-out metrics report |
| Demo-complete app | End of Day 8 | Full replay in Streamlit |
| Submission-ready package | End of Day 10 | README, deck, recording, rehearsal |

## 3-minute live demo script

1. **Hook (0:00–0:20):** “Fraud losses often arrive as coordinated bursts. Static transaction rules can miss that stream-level signal.”
2. **Replay (0:20–1:20):** Start normal traffic, let the spike emerge, and point to the alert plus detection latency.
3. **Trust (1:20–1:50):** Open the alert detail and explain the safe, aggregate signals behind it—unusual velocity and repetitive behavior—not proprietary-style raw thresholds.
4. **Business proof (1:50–2:35):** Show held-out precision/recall/PR-AUC and the cost curve. “We chose the operating point that minimizes expected ₹ loss, rather than chasing F1.”
5. **Close (2:35–3:00):** State the defense-only guardrails, transparent limitations of public/synthetic data, and the next production step: validate against merchant-specific historical streams with human-review feedback.

## Risks and guardrails

| Risk | Mitigation |
|---|---|
| Dataset access blocks progress | Use the alternate named dataset immediately; do not spend more than 90 minutes troubleshooting access. |
| Weak Isolation Forest performance | Keep the baseline and lead with the honest comparison plus cost framing. A reliable baseline beats an unfinished advanced model. |
| Synthetic spikes feel artificial | Use several seeded scenario families, disclose them, and make no claim that they are production fraud labels. |
| UI work consumes ML time | Start Streamlit only after the held-out report is saved on Day 7. |
| Demo failure | Keep a local backup recording and precomputed artifacts; avoid internet-dependent demo steps. |
| Safety concern | Never expose raw thresholds/weights, injection controls, or feature combinations that enable evasion. |

## Stretch goal rule

Only attempt an autoencoder or deployment enhancement after all Definition of Done boxes are checked. Cap it at **two hours**. If it does not produce a clearer held-out improvement and a simple story, omit it from the submission.

## Daily operating rhythm

- [ ] Begin each day by running the current pipeline and recording any breakage before coding.
- [ ] End each day by updating the relevant report/readme, checking off completed items, and committing a runnable increment.
- [ ] Keep a `DECISIONS.md` log for dataset choice, feature/window choice, cost assumptions, and threshold selection.
- [ ] Protect the last 15 minutes each day for tomorrow’s first task; this prevents context-switching from consuming the next session.
