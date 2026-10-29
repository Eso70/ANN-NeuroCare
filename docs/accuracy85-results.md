# Requested 85% accuracy policy — 29 October 2026

Historical report: superseded by the [recall-focused restoration](recall-policy-results.md).
This accuracy-first variant remains intact for offline inspection; it is no longer
the configured default or accepted by public 2021 inference. Instructions below describe
the historical experiment, not the current deployment policy.

Configured artifact: `artifacts/20261028T224006Z-009a4823`.

**Measured test accuracy is 85.0109%, but recall is only 13.9527%.** The classifier
missed 5,390 of 6,264 positive survey labels. This is an accuracy-prioritizing decision
policy for an educational classifier, not an improvement in learned ranking or evidence
of clinical usefulness. The same 2021 ANN weights and preprocessing are retained from
`20261028T222429Z-e5a45f4d`; no further training took place in this request.

## What changed

The user changed the objective from the earlier recall-preserving comparison to an
explicit request for at least 85% overall accuracy. That is a materially different
operating point. The prior 2021 ANN used cutoff 0.132128. The new version uses
**0.49337536096572876**, chosen from validation data only.

The written protocol is `accuracy85-plan.md`. A cutoff retaining maximum validation
recall at 85.5% validation accuracy was infeasible. Validation did permit 85%; before
test evaluation, the fallback objective was recorded as maximum validation accuracy,
with ties favoring recall and then the higher cutoff. This selected 85.1176% validation
accuracy and 14.8254% validation recall. The cutoff, weights checksum and validation
metrics were frozen before the new test evaluation. It was not adjusted from test results.

The test partition has been evaluated previously. This is **not fresh independent
validation**. The 85.01% result is a measured point estimate on these records, not a
guarantee of 85% accuracy for future data. No statistical improvement in learned
discrimination is claimed. The protocol and generated artifact are inspectable; no
test labels were used to choose the cutoff.

## Same 40,376 test rows; same 2021 ANN weights

| Metric | Previous recall-focused cutoff | New accuracy-focused cutoff |
| --- | ---: | ---: |
| Accuracy | 67.0423% | 85.0109% |
| Recall | 82.8225% | 13.9527% |
| Precision | 29.7836% | 56.9010% |
| Specificity | 64.1446% | 98.0593% |
| ROC AUC | 0.812885 | 0.812885 |
| Average precision | 0.429336 | 0.429336 |
| Brier score | 0.107429 | 0.107429 |
| True negatives / false positives | 21,881 / 12,231 | 33,450 / 662 |
| False negatives / true positives | 1,076 / 5,188 | 5,390 / 874 |

Majority-only accuracy on these same rows is 84.4858% with zero positive recall.
The new policy correctly classifies 212 more rows than that baseline. It exceeds
the requested 85% by approximately 0.011 percentage points, a narrow margin.
It still misses about 86% of positive labels. Accuracy alone would conceal this cost.
The historical 68.96% result belongs to a different 2015 test cohort and is not a
direct before/after comparison with these new-year results.

## Correct source and public contract

The 2021 data uses the documented conversion in `app/ml/brfss2021.py`. Its target
is DIABETE4 yes=1, with no/pregnancy-only/borderline coded 0; unknown/refused responses
were excluded. Income uses 2021 nominal US dollars, with upper categories combined.
These source meanings are now supplied by the model contract endpoint and shown
on the methodology page and input labels. The legacy 2015 model still gets its
original contract when selected. Numeric payload fields, ranges and all 21 inputs
remain unchanged, so no database migration is required.

Unreviewed 2021 experimental artifacts remain blocked by the API. Only explicitly
reviewed accuracy variants with valid metrics, nonzero positive recall and accuracy
above both 85% and the majority baseline are accepted. The public API exposes the
accuracy-prioritizing policy and measured recall notice. The same notice is returned
with predictions and displayed prominently with results. The homepage shows accuracy
beside recall; the full model evaluation shows accuracy, recall, precision and AUC.
The existing design, multi-step form and hidden scrollbar behavior were retained.

## Checks actually executed

- Generic artifact audit passed: training-only scaling, dataset/model hashes, disjoint
  partitions, validation-selected cutoff and recomputed validation/test metrics.
- The parent 2021 lineage audit was rerun and passed, including raw/derived checksums,
  per-row source lineage and absence of historical profiles from the 2021 held-out sets.
- File hashes confirm the model, cohort, splits and source indices are byte-identical
  to the audited 2021 parent; preprocessing statistics also match exactly.
- **113 backend tests passed, 3 HTTP cases deselected**, using the new artifact through
  a process-local MODEL_DIR override before changing root configuration. Tests included
  real Keras reload/inference, contract source years, validation threshold optimization,
  strict inputs, policy notices, public-route privacy and service persistence behavior.
- Backend Ruff passed. Frontend **25 tests passed**, ESLint passed, explicit TypeScript
  checking passed and the production build passed.
- Root `.env` changed only MODEL_DIR. All unrelated environment bytes were checked
  unchanged; credentials were not printed. Original artifacts and data remain intact.
- A fresh process loaded the changed root configuration and verified actual Keras
  inference, API-function metadata, the matching 2021 public contract and income label.
  Direct live-HTTP verification was blocked by local socket access (WinError 10013).

No real database write, migration, browser UI sweep or live service restart is claimed
for this change. Direct model/API-function verification is separate from live HTTP
and PostgreSQL integration. Restart the existing project launcher from a normal local
terminal so its cached settings use the new model:

```powershell
.\scripts\dev.ps1 start
```

If the old launcher is running, stop that launcher with Ctrl+C first. PostgreSQL should
remain running. After restart, `/api/v1/model` should report version
`20261028T224006Z-009a4823`, contract `cdc-brfss2021-binary-v1` and cutoff approximately
0.493375. Existing prediction records retain their original model version.

## Reproduce or restore the previous operating point

From `backend/`, create a separate, unpromoted policy artifact:

```powershell
.\.venv\Scripts\python.exe -m app.ml.accuracy_target --parent ../artifacts/20261028T222429Z-e5a45f4d --output ../artifacts
```

The command never edits `.env` or auto-promotes a result. Review the measured tradeoff
and source contract before enabling another artifact. To restore the previously
configured 2015 model, set root `.env` MODEL_DIR to its preserved absolute path:

```dotenv
MODEL_DIR="D:/Coding - Projects/NeuroCare/artifacts/20261028T214854Z-8612419f"
```

Restart the project API after changing the setting. This selects the original model
and its original 2015 source meanings; it does not alter prediction history.

The statistical-model/decision-policy distinction is described in the official
[scikit-learn threshold guide](https://scikit-learn.org/stable/modules/classification_threshold.html).
The official [TensorFlow imbalanced-data tutorial](https://www.tensorflow.org/tutorials/structured_data/imbalanced_data)
also explains why accuracy must be read alongside precision and recall.
