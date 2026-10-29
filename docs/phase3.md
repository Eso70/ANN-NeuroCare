# Phase 3 — CDC integration and real ANN training

**Historical original run:** the active model cutoff and database status have since
been corrected. See [latest fixes and verification](fixes.md). The fixed-0.5 metrics
below remain the original version's results, not the active model's classification metrics.

The existing architecture now supports the supplied CDC dataset. This phase does not
add authentication, public deployment, history browsing, or a replacement application.
Pima examples in Phase 2 documentation are historical and incompatible with this model.

## Dataset and input contract

Source: [Alex Teboul, Diabetes Health Indicators Dataset](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset),
derived from CDC BRFSS 2015. The untouched file is
`data/diabetes_binary_health_indicators_BRFSS2015.csv`. SHA-256:
`19f367e3e3350768f0c144c5d73ee5b355f67a57eaaa86ca7bd8aec594d8b1d0`.
Preserve attribution and follow the source's usage terms.

253,680 rows; labels: 218,334 zero and 35,346 one; 21 input fields. There are
229,474 distinct full rows and 227,908 distinct feature profiles. Repeated profiles
are preserved, including profiles with differing labels.

The shared contract in `backend/app/ml/data.py` validates integer source codes,
missing/non-finite values, extra columns and ranges. Zero is a valid survey response;
Pima zero-imputation is removed. BMI accepts source-range integers 12-98, not a clinical
validity range. Age uses 13 bands, not years. Income and education use categorical
codes. The browser fetches field definitions/options from `GET /api/v1/model/contract`;
the Pydantic schema uses the same definitions. No names or patient references are accepted.

The target is the stored `Diabetes_binary` label. UCI describes it as prediabetes/diabetes
combined, but descriptions alone do not establish the original recoding. The interface
conservatively reports dataset class/score. Verify the original cleaning notebook before
assigning a more specific clinical interpretation; class 0 must not imply healthy.

Historical self-reported US survey data has selection/reporting bias, coarse ordinal
inputs, imbalance and socioeconomic variables. This CSV does not supply survey design
weights. It cannot establish future onset, causality, clinical validity or generalization
to an Iraqi population. Dataset codes are modeling inputs, not clinical advice.

## Leakage controls and training

Five stratified group folds keep identical feature profiles together even when labels
differ: three folds train, one validation, one test. This prevents exact-profile leakage
without assuming matching profiles identify the same individual. Saved split indices
cover every row once; the executed audit verified zero profile overlap between splits.

Training-only means/standard deviations scale all inputs. Ordinal codes are treated as
ordered numbers, an equal-spacing assumption and baseline limitation. No oversampling,
undersampling, class weighting or test-based threshold tuning occurs.

ANN: 21 inputs, Dense(32, ReLU), Dropout(0.2), Dense(16, ReLU), Dense(1, sigmoid).
Adam, binary cross-entropy, batch size 512, seed 42, maximum 30 epochs. Validation loss
selects best weights with early-stopping patience 5; this run stopped at 21 epochs.
A logistic-regression baseline uses the same splits/preprocessing. Test evaluation
occurs after fitting at the preselected 0.5 threshold. Do not repeatedly tune against
this test partition based on the results below.

## Measured evaluation

Saved model: `artifacts/20261027T203103Z-5eefa372`. Metadata contains hashes,
preprocessing, contract, feature order, dependencies, source, split sizes and measured
results. `split_indices.npz` preserves the row assignments. Split sizes: train 152,419,
validation 50,360, test 50,901.

| Metric | ANN | Logistic regression |
| --- | ---: | ---: |
| Accuracy | 86.99% | 86.65% |
| Precision | 59.93% | 52.27% |
| Recall | 11.78% | 16.05% |
| ROC AUC | 0.8251 | 0.8162 |
| Average precision | 0.4167 | 0.3905 |
| Brier score | 0.09553 | 0.09798 |

Majority-class test accuracy: 86.46%. Confusion matrix (actual rows/predicted columns
in [0,1] order): TN 43,467; FP 543; FN 6,079; TP 812.

**At threshold 0.5 this model misses 88.22% of positive test examples. It is unsuitable
for screening.** It is configured locally only for an educational demonstration. Its
sigmoid output is not established as a calibrated personal probability. The form shows
actual saved accuracy, majority baseline, recall, ROC AUC and version from
`GET /api/v1/model`. There are no invented metrics or simulated predictions.

## Run and reproduce

The root `.env` now selects this model with absolute MODEL_DIR; other credentials
were preserved. Restart any existing FastAPI process after changing model versions.
From the project root in PowerShell:

```powershell
.\scripts\dev.ps1 db-start
# Only when neurocare_db does not exist:
.\scripts\dev.ps1 db-create
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 backend
```

In another terminal: `.\scripts\dev.ps1 frontend`. Visit
http://localhost:5173/predictions and enter synthetic demonstration values only.
A prediction returns 201 only after persistence; database/model failures return 503.
Model metadata does not require database access.

Reproduce training from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.ml.train --csv ../data/diabetes_binary_health_indicators_BRFSS2015.csv --source 'Alex Teboul; CDC BRFSS 2015; https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset' --output ../artifacts --epochs 30
```

Each run creates a new version. Review it before explicitly updating MODEL_DIR.
Old format/feature contracts are rejected. Loading verifies model SHA-256, dimensions,
and preprocessing. Use trusted local artifacts only.

## Checks

From `backend/`:

```powershell
$env:RUN_MODEL_TESTS='1'
.\.venv\Scripts\python.exe -m pytest tests/test_ml_data.py tests/test_prediction_service.py tests/test_model_artifact.py -q
Remove-Item Env:RUN_MODEL_TESTS
.\.venv\Scripts\python.exe -m ruff check app tests
```

Once database connectivity/migrations work, set `RUN_DB_TESTS=1` and `RUN_ML_TESTS=1`
and run the full suite. That verifies real inference plus the saved database row, then
deletes its own test record. `scripts/dev.ps1 check` runs frontend build/lint and backend lint.
Runtime socket restrictions can block PostgreSQL clients and HTTP TestClient startup;
a passing artifact/service test does not prove browser or PostgreSQL integration.

## Executed Phase 3 results (2026-10-27)

- Training on the full supplied CSV succeeded; saved model reload and repeated inference passed.
- Dataset hash, complete row partition and zero cross-split profile overlap verified.
- Full backend suite with `RUN_MODEL_TESTS=1`: **31 passed, 2 skipped** in 7.50 seconds.
  The two skips require real PostgreSQL (health/schema and persisted-model prediction).
- HTTP TestClient checks now pass, including contract retrieval, input errors, missing model
  behavior, and metadata returned exactly from saved measured evaluation results.
- Backend Ruff and Python source compilation passed.
- Frontend TypeScript/Vite production build and ESLint passed after the final UI changes.
- One dependency deprecation warning concerns Starlette's AnyIO BlockingPortal alias;
  it did not fail the suite. No dependency upgrades were attempted to suppress it.
- PostgreSQL `createdb` reached a server and reported `neurocare_db` already exists.
  Subsequent SQLAlchemy connections timed out on localhost; Alembic upgrade failed for
  that reason. Migrations, table existence and real persistence are **not verified**.
- A browser interaction was not performed; frontend build and HTTP API tests do not
  substitute for a real browser/database demonstration.

The wider university-demonstration review requested afterward remains deferred while
Phase 3 is completed, as instructed.
