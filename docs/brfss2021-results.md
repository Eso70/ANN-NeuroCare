# BRFSS 2021 data and training results — 29 October 2026

Historical experiment report. A later accuracy-first experiment was retired for low recall;
see [the current recall policy report](recall-policy-results.md) for the configured model,
tradeoff and checks.

The new data was used for conversion, training and a fresh-wave model comparison.
It **did not improve measured accuracy**, so the application's current 2015 model
`20261028T214854Z-8612419f` remains configured. The 2021 candidate is preserved for
offline study at `artifacts/20261028T222429Z-e5a45f4d`.

## Data location and conversion

- Moved the supplied `LLCP2021.XPT` from the project root into `data/raw/`.
- Original size: 1,055,538,560 bytes; 303 columns and 438,693 survey responses.
- Raw SHA-256: `ae7fea17e09740fd2bd306b217c58df42d86060eab85baf0d6af67e977a1eca2`.
- Derived CSV: `data/processed/diabetes_binary_health_indicators_BRFSS2021.csv`.
- The adjacent JSON records the raw/CSV hashes, exact code mappings, overlapping
  missingness counts, exclusions and provenance.
- Retained 236,376 complete cases: 202,810 label 0 and 33,566 label 1.
  Excluded 202,317 incomplete/unsupported records from derived training data; the
  raw source remains intact. This substantial exclusion can introduce selection bias.

Definitions were checked against the official [CDC 2021 codebook](https://www.cdc.gov/brfss/annual_data/2021/pdf/codebook21_llcp-v2-508.pdf)
and [variable layout](https://www.cdc.gov/brfss/annual_data/2021/llcp_varlayout_21_onecolumn.html).
Unknown/refused responses remain missing and are excluded, not converted to No.
Only health-day code 88 becomes zero. `_BMI5` has two implied decimal places and
is rounded to an integer; values outside the existing 12–98 input range are excluded.
Upper income categories collapse to the existing eight bands, in **2021 nominal
USD**, without inflation adjustment. The target is explicitly DIABETE4 yes=1;
no/pregnancy-only/borderline=0. This target is not claimed to have a verified identical
definition to every published description of the historical cleaned 2015 file.

The years were therefore not blindly concatenated. One candidate trained from
scratch; another transferred the existing ANN weights and fine-tuned on 2021 labels.
Transfer first-layer weights/biases were algebraically adapted to new training-only
scaling, and initial function equivalence was checked before training.

## Leakage protection and selection

The protocol was written in `brfss2021-training-plan.md` before test evaluation.
13,776 new-year records matching old validation/test profiles were quarantined.
20,789 records matching prior training profiles were assigned only to training.
Fresh validation/test profiles are absent from the entire original 2015 CSV.
Feature profiles are not verified person identifiers; this does not establish that
all respondents are new people. The resulting holdout is a novel-profile cohort,
not a survey-weighted representative sample of the 2021 population.

The final 222,600-row cohort is retained as the candidate's `training_cohort.csv`.
Splits: **141,834 train / 40,390 validation / 40,376 test**. Scaling fits training
only. Both candidates use 64/32 ReLU layers, dropout 0.1 and L2 0.0001, natural
cohort class frequencies, Adam and binary cross-entropy. No survey weights were used.
The initial learning rates were 0.001 for fresh training and 0.0001 for transfer.
Both had a 60-epoch ceiling, validation-loss early stopping with patience 8 and a
plateau learning-rate schedule. Completed epochs: fresh 34, transfer 19.

Validation threshold selection maximized accuracy subject to at least 83.25397%
recall, the parent's measured new-wave validation recall. The transfer candidate
won on validation accuracy: 67.3137%, versus 67.1305% for fresh initialization.
Model, cutoff and checksum were frozen before first fresh-test inference. No search
was repeated after seeing test results. The parent's cutoff was also selected on
validation at the same recall requirement for a fair operating-point comparison.

## Same-cohort fresh-test results

| Metric | Current ANN on new holdout | Selected 2021 candidate |
| --- | ---: | ---: |
| Accuracy | 67.0745% | 67.0423% |
| Recall | 82.3116% | 82.8225% |
| Precision | 29.7313% | 29.7836% |
| Specificity | 64.2765% | 64.1446% |
| ROC AUC | 0.811436 | 0.812885 |
| Average precision | 0.425724 | 0.429336 |
| Brier score (lower is better) | 0.107816 | 0.107429 |
| TN / FP | 21,926 / 12,186 | 21,881 / 12,231 |
| FN / TP | 1,108 / 5,156 | 1,076 / 5,188 |

The candidate found 32 additional positives but produced 45 additional false positives:
13 fewer correct classifications overall. Accuracy changed by **−0.0322 percentage
points**; recall increased by **0.5109 points**. A paired profile-cluster bootstrap
(2,000 draws, seed 42) gave an accuracy-difference 95% interval of approximately
**−0.1807 to +0.1139 percentage points**. This does not establish an accuracy improvement.

The original 68.96% reported accuracy used a different 2015 test cohort. It cannot
be compared directly with these new-year percentages. The current model's original
saved metrics remain unchanged; the table compares both models on identical new rows.

The candidate failed the predeclared requirement of higher observed test accuracy
with no decrease in recall. `.env` was not changed. Original data, artifacts, database
configuration and prediction records remain preserved. The API refuses this offline-
only 2021 contract so its income-year/target meanings cannot silently appear behind
the active 2015 form. Promotion would require matching contract/source UI changes
and evidence supporting that decision; this failed candidate was not promoted.

## Verification and reproducibility

`app.ml.audit_2021` passed. It recomputed candidate and parent test metrics, checked
training-only scaling and validation-selected cutoffs, verified raw/CSV/model hashes,
checked each cohort row against its source index, checked complete/disjoint partitions,
and confirmed zero prior-profile overlap in the fresh held-out splits. The saved
report is `docs/brfss2021-audit.json`.

Re-run the existing experiment from `backend/` to create a separate artifact:

```powershell
.\.venv\Scripts\python.exe -m app.ml.train_2021 --csv ../data/processed/diabetes_binary_health_indicators_BRFSS2021.csv --old-csv ../data/diabetes_binary_health_indicators_BRFSS2015.csv --parent ../artifacts/20261028T214854Z-8612419f --output ../artifacts --epochs 60
```

The converter refuses to overwrite existing derived files. To independently rebuild
the CSV, choose a new output filename:

```powershell
.\.venv\Scripts\python.exe -m app.ml.brfss2021 --xpt ../data/raw/LLCP2021.XPT --output ../data/processed/brfss2021-rebuild.csv
```

Do not repeatedly optimize against the already viewed holdout and call it independent
validation. The search commands never modify `.env` or auto-promote a model. The
original `app.ml.train` CLI rejects a 2021 conversion manifest to avoid incorrectly
labeling that model as 2015.

Final backend checks: **91 passed, 3 HTTP cases deselected** in the selected config,
setup, evaluation, data, new-year conversion/splitting/transfer, service, public-contract
and real-artifact suites. Ruff passed. This is not a claim that the full database/HTTP
integration suite ran. Final preservation checks confirmed unchanged `.env`, both
launcher scripts and the configured original model checksum, and confirmed the raw
file is present in its new location and absent from the root.

No frontend design changes, live browser request, database write or service restart
were performed for this experiment.
