# Recall-focused default restored - 29 October 2026

Reviewed artifact: `artifacts/20261029T043159Z-bd9e866c`.

The 85% accuracy operating point was retired because it detected only 13.95% of
positive labels. The current default restores the previously selected 2021 cutoff
**0.132127583026886**, using a new artifact version and unchanged ANN weights.
This does not improve learned discrimination or establish clinical usefulness.

## Selection and safeguards

The [recorded plan](recall-policy-plan.md) restores the original parent
`20261028T222429Z-e5a45f4d` without another threshold search. The original objective
maximized validation accuracy subject to its saved 83.253968% validation recall floor.
The generic independent audit recomputed that selection and its validation/test
metrics. The existing test partition has been evaluated previously; this is not new
independent validation. The cutoff was not adjusted after test review.

Public 2021 inference now requires explicit `recall_policy_reviewed` status,
validation-only selection, a saved validation recall floor of at least 80%, validation
recall meeting that floor, and measured test recall of at least 80%. The test check
is for deployment review, never threshold optimization. **80% is a project review
guard, not a medical standard, certification or guarantee of future performance.**
The retired accuracy-first review marker no longer enables public 2021 inference.
Unreviewed experimental artifacts remain blocked. Historical 2015 contracts remain
supported for their original source semantics.

## Same 40,376 test records and weights

| Metric | Retired accuracy-first cutoff | Restored recall-focused cutoff |
| --- | ---: | ---: |
| Accuracy | 85.01% | 67.04% |
| Recall | 13.95% | 82.82% |
| Precision | 56.90% | 29.78% |
| Specificity | 98.06% | 64.14% |
| ROC AUC | 0.8129 | 0.8129 |
| Average precision | 0.4293 | 0.4293 |
| Brier score | 0.10743 | 0.10743 |
| True negatives | 33,450 | 21,881 |
| False positives | 662 | 12,231 |
| False negatives | 5,390 | 1,076 |
| True positives | 874 | 5,188 |

The restored cutoff misses fewer positive survey labels but produces many more false
positives. Only about 30% of its positive predictions match a positive survey label.
An all-negative rule would score 84.49% accuracy while detecting none of the positive
labels; overall accuracy alone is a poor objective for this intended demonstration.
The score is not established as a calibrated individual probability, a negative output
does not rule out disease, and the application remains an educational prototype.

## Preserved behavior

The new artifact's model, cohort CSV, source indices and split archive are byte-identical
to the 2021 parent, and preprocessing matches exactly. Original 2015, 2021 and
accuracy-first artifacts remain intact. The 21 numeric fields, 2021 source/income
semantics, database schema, stored predictions, frontend design, scrolling behavior
and launcher are preserved. Result notices and methodology text explicitly disclose
the measured recall, accuracy, precision and false-positive tradeoff.

Only `MODEL_DIR` is switched in root `.env`; unrelated settings and credentials are
preserved byte for byte. No dataset, database record or database service is modified.

## Verification and restart

See [the audit](recall-policy-audit.json) and [review record](recall-policy-review.json)
for the executed checks. The audit verifies hashes, full/disjoint split coverage,
no cross-split identical profiles, training-only scaling, original validation-selected
cutoff and recomputed metrics. **127 selected backend tests passed; 3 HTTP cases were
deselected.** These included real Keras reload/inference, review guards, strict inputs
and prediction-service persistence behavior. Backend Ruff passed. **25 frontend tests
passed**, as did ESLint and the TypeScript/production build. A fresh process loaded the
changed root `.env` and verified real inference with the restored cutoff, API-function
metadata, the matching 2021 contract, rejection of the retired accuracy-first variant,
and preserved prior-model checksums. A direct live HTTP request failed with local
socket PermissionError `WinError 10013`. No live HTTP or database integration success
is implied.

No live service restart, browser verification or real database write is claimed.
Stop the existing project launcher with Ctrl+C, then start it from the root:

```powershell
.\scripts\dev.ps1 start
```

PostgreSQL should remain running. A healthy reused API retains cached settings until
restarted. After restart `/api/v1/model` should report version
`20261029T043159Z-bd9e866c` and threshold approximately `0.132128`.
Existing prediction rows retain their original model versions.

To rerun the independent audit from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.ml.audit --output ../docs/recall-policy-audit.json
```

The procedure follows the distinction between statistical scores and decision policies
in the [official scikit-learn guide](https://scikit-learn.org/stable/modules/classification_threshold.html).
The [official TensorFlow imbalance tutorial](https://www.tensorflow.org/tutorials/structured_data/imbalanced_data)
also explains why accuracy must be read alongside recall and precision.
