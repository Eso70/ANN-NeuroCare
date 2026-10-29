# ANN accuracy comparison — 29 October 2026

Historical experiment report. A later accuracy-first experiment was retired for low recall;
see [the current recall policy report](recall-policy-results.md) for the configured model,
tradeoff and checks.

Three new ANN configurations were trained on the existing 253,680-row CSV.
The configured model is now `artifacts/20261028T214854Z-8612419f`.
The original `20261027T204111Z-db7cb83c` artifact is preserved.

## Selection and measured results

The exact parent partitions were reused: 152,419 training rows, 50,360 validation
rows and 50,901 test rows. Identical feature profiles remain in a single partition.
The dataset SHA-256 and training-only scaling were checked before fitting.

The validation recall floor was frozen at the original model's measured validation
recall, 0.8392454954954955. Each candidate's threshold maximized validation accuracy
subject to that floor. Ties prefer greater recall, then the higher cutoff. Candidate
selection used validation accuracy, then average precision, then lower Brier score.
Only the selected candidate was evaluated on test data; no test result selected a
configuration or cutoff. No additional search was performed after seeing test results.

| Configuration | Hidden units | Dropout per hidden layer | L2 | Initial learning rate | Completed epochs | Validation accuracy | Validation recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wide (selected) | 64, 32 | 0.10 | 0.0001 | 0.001 | 33 | 68.7153% | 83.9245% |
| deep | 128, 64, 32 | 0.15 | 0.0001 | 0.0005 | 59 | 68.6934% | 83.9245% |
| compact | 32, 16 | 0.05 | 0.00001 | 0.001 | 38 | 68.5425% | 83.9245% |

Training used Adam, binary cross-entropy, batch size 512, seed 42 and up to 60 epochs.
Early stopping monitored validation loss with patience 8 and restored the best weights.
Learning rate halved after 3 epochs without improvement, with a minimum of 0.00001.
Output bias started at the training class log odds. Natural class frequencies were retained.
CPU/data threads were bounded. Search settings and epoch histories are saved in the
candidate's `search.json`; the final manifest contains its checksum and training settings.

| Test metric | Original ANN | Selected ANN |
| --- | ---: | ---: |
| Accuracy | 68.8709% | 68.9633% |
| Precision | 28.0324% | 28.1445% |
| Recall | 82.9052% | 83.2245% |
| Specificity | 66.6735% | 66.7303% |
| ROC AUC | 0.825109 | 0.826497 |
| Average precision | 0.416656 | 0.420807 |
| Brier score (lower is better) | 0.095535 | 0.095269 |
| Cutoff | 0.128489 | 0.118681 |
| True negative / false positive | 29,343 / 14,667 | 29,368 / 14,642 |
| False negative / true positive | 1,178 / 5,713 | 1,156 / 5,735 |

This is a **small measured improvement**: 47 more correct classifications, comprising
25 fewer false positives and 22 fewer false negatives. It does not establish a reliable
generalization improvement or clinical usefulness. The same development test partition
was reported previously; it is not a fresh independent validation. No statistical
significance claim is made. A majority-only classifier has 86.46% accuracy but zero
positive recall. Raising the original cutoff to 0.5 previously gave 86.99% accuracy
and only 11.78% recall; that shortcut was not used for the new configured model.

## Changes and executed checks

- Added `python -m app.ml.improve` for the bounded, reproducible comparison. It does
  not alter `.env` or auto-promote candidates.
- Added recall-constrained validation threshold selection and extended the audit to
  recompute either the original F2 policy or the new recall-constrained policy.
- Independently recomputed both artifacts' dataset hashes, split coverage, profile
  overlap, training scaling, validation cutoffs, validation metrics and test metrics.
  Both audits passed: `accuracy-parent-audit.json` and `accuracy-candidate-audit.json`.
- Configured only `MODEL_DIR` in root `.env` after the candidate passed its audit and
  its observed test accuracy and recall exceeded the parent's. Unrelated configuration
  bytes were checked unchanged. The original model checksum still matches its manifest.
- A reload check initially caught dotenv interpreting `\a` in a double-quoted Windows
  path. `MODEL_DIR` was corrected to forward slashes, and all 8 selected real-artifact
  load/inference/checksum/contract tests then passed using the configured model.
- Backend evaluation/data tests: **26 passed**. Config/setup/service/public-contract
  tests: **42 passed**. Real-artifact tests: **8 passed, 3 deselected**. Ruff passed.
- Frontend regression tests: **22 passed**. ESLint and production build (including
  TypeScript compilation) passed. Architecture and cutoff copy now use backend metadata;
  Phase 7 styling and hidden-scrollbar behavior were retained.

No database was connected to or changed during this work. Database persistence and
HTTP/browser integration were not rerun. Direct loopback checks for ports 8000/5173
were blocked with WinError 10013, and CIM process inspection was denied. Consequently,
no running application process was stopped/restarted and no live API switch is claimed.
No new browser visual verification is claimed for this change.
The single-command launcher was attempted and exited at the existing 5432 guard after
its service check could not confirm connectivity. It did not launch or stop PostgreSQL.

To load the new configuration, stop the existing project launcher with Ctrl+C, then run:

```powershell
.\scripts\dev.ps1 start
```

Confirm version `20261028T214854Z-8612419f` and cutoff approximately 0.118681 in the
model information. Existing prediction rows keep their original recorded model version.

## Additional data for the next round

The current data was sufficient for this comparison. A useful next step is a separate
survey year for fresh evaluation and, after compatibility checks, additional training.
The official [CDC BRFSS 2021 page](https://www.cdc.gov/brfss/annual_data/annual_2021.html)
lists 438,693 survey records and provides the SAS Transport download:

- [LLCP2021XPT.zip](https://www.cdc.gov/brfss/annual_data/2021/files/LLCP2021XPT.zip)
- [2021 codebook](https://www.cdc.gov/brfss/annual_data/2021/pdf/codebook21_llcp-v2-508.pdf)

Put the ZIP in `data/raw/` without replacing the 2015 CSV. The 2021 variable layout
includes blood pressure, cholesterol, diabetes, fruit/vegetable and other relevant
survey fields. It is **not a drop-in CSV**: category/target definitions, missing-value
codes, income categories/year and question changes require explicit review and a
documented converter before combining years. Reserve a fresh evaluation partition
before any tuning. More rows do not guarantee higher accuracy.
