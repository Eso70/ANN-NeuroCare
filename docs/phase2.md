# Phase 2: offline ANN workflow and persisted model demonstrations

## Scope and current status

Phase 2 was explicitly requested after the Phase 1 blockers were reported. Implemented:
CSV validation, train-only imputation/scaling, an offline TensorFlow ANN training CLI,
versioned artifacts with measured holdout evaluation, a real inference endpoint,
PostgreSQL persistence, and a responsive demonstration form.

**No dataset was supplied, no ANN was trained, and no model metrics were generated.**
Initial registry installation retries failed, but dependencies and resolved lock files
became available later in the session. TensorFlow 2.19 imports successfully, `pip check`
passes, and the frontend production build plus ESLint and backend Ruff checks pass.
PostgreSQL startup reports success, but client connections remain denied by the sandbox
(Windows socket error 10013), so database creation and migrations remain blocked.
Source completion does not mean runtime acceptance has passed.

## Dataset contract

Supply a legally usable, de-identified educational CSV at `data/diabetes.csv`. No automatic
dataset download or fabricated training data is provided. This implementation assumes
the common eight-feature Pima-format contract; confirm that your source actually uses
these definitions and target encoding before training. It is not a generic healthcare
CSV importer. The parser rejects additional columns, including identifying metadata.

| CSV column | Expected definition |
| --- | --- |
| Pregnancies | Number of pregnancies |
| Glucose | Dataset plasma glucose measurement, mg/dL |
| BloodPressure | Diastolic blood pressure, mm Hg |
| SkinThickness | Triceps skinfold thickness, mm |
| Insulin | Dataset 2-hour serum insulin, µU/mL |
| BMI | Body mass index, kg/m² |
| DiabetesPedigreeFunction | Source dataset's calculated pedigree score |
| Age | Age in years |
| Outcome | Binary dataset label, 0 or 1; confirm source semantics |

Column order in CSV can vary; inference always uses the fixed feature order in code.
All cells must be numeric, features finite/nonnegative, and Outcome binary. Empty cells,
duplicate feature rows, extra columns, fewer than 100 unique rows, or fewer than 20
examples per class cause explicit errors. Resolve data issues using source documentation,
not blind deletion. The minimum sample count is a mechanical split safeguard, not evidence
of adequate statistical power. The API additionally requires integer pregnancy/age values
and broad numeric caps to reject obviously invalid requests; these are not clinical ranges.

Zero means missing for glucose, blood pressure, skin thickness, insulin and BMI only.
Zero pregnancies remains a real zero. If your dataset uses a different missing-value
convention or population, revise the contract before training. There is no CSV upload API.

The code cannot identify repeated people with different measurements; use a source with
one independent row per individual, or implement group splitting before using longitudinal
data. Dataset-specific population restrictions must be recorded in the source notes.

## Training and evaluation

Install the dependencies and resolve database setup using README.md first. From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.ml.train --csv ../data/diabetes.csv --source 'Dataset URL, license, target meaning, population restrictions' --output ../artifacts --epochs 100
```

The fixed seed is 42. Stratified train/validation/test proportions are 60/20/20. Medians,
means and population standard deviations are fitted exclusively on training rows.
Validation loss drives early stopping (patience 10, best weights restored). The ANN has
16 and 8 ReLU hidden units, dropout 0.2, and a sigmoid output, trained with Adam/binary
cross-entropy. The threshold is fixed at 0.5. The test set is evaluated after fitting;
do not repeatedly tune experiments against those test results.

Each run produces a unique `artifacts/<version>/` containing `model.keras` and
`metadata.json`. Metadata records feature order, preprocessing statistics, data/model
SHA-256 hashes, provenance, seed, dependency versions, split sizes, completed epochs,
and actual test accuracy, precision, recall, ROC AUC, average precision, Brier score,
confusion matrix and majority-class accuracy. Confusion matrix order is [0, 1].
Inspect class balance and recall as well as accuracy; none of these metrics establish
clinical validity. Seeds do not guarantee identical results across hardware/library changes.

The manifest is written last; incomplete runs cannot load. Models are never auto-promoted.
Review evaluation and source limitations before selecting a version. The loading checksum
detects accidental mismatches, not malicious artifacts; use only your trusted local output.

## Configure and run

Set the following in the root `.env` using the **absolute path printed by training**:

```dotenv
MODEL_DIR=D:/Coding - Projects/NeuroCare/artifacts/your-version
```

Start the database, apply the Phase 1 migration, then restart the backend and frontend:

```powershell
.\scripts\dev.ps1 db-start
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 backend
# In another terminal:
.\scripts\dev.ps1 frontend
```

Open http://localhost:5173/predictions. Use synthetic inputs only. Empty MODEL_DIR disables
inference; absent/incompatible/corrupt artifacts return 503 with no fake output. The model
loads lazily and is cached per process; restart FastAPI when changing model versions.

`POST /api/v1/predictions` accepts the eight feature fields as a JSON object. It rejects
extra fields, returns 422 for invalid inputs, 503 for unavailable model/database, and 201
only after saving a row in the existing predictions table. The response includes the row
ID, class, model output, model version, and an educational-use notice. There is no schema
change in this phase, so only migration 0001 is required. No patient reference is accepted.

There are no authentication or public deployment changes. History browsing and clinical
decision support remain outside scope. Requests are not automatically retried: a lost
response can occur after commit, so retries may create multiple demonstration rows.

## Verification

Executed in this session: **9 standard-library data/preprocessing tests passed**, Python
source compilation passed, and the training CLI `--help` completed successfully. Frontend
production build and ESLint passed, backend Ruff passed, TensorFlow imported successfully,
and pip reported no broken requirements. The complete HTTP test suite was interrupted:
faulthandler showed it stalled in Windows `socket.socketpair` during TestClient's event
loop startup. This is distinct from passing or failing the application assertions.
No training, model evaluation, real API persistence integration, or browser result is
claimed as passing. Direct data/service tests are run separately from HTTP tests.

The separate pytest run completed with **15 passed in 0.53s** across `test_ml_data.py`
and `test_prediction_service.py`. It covers CSV/preprocessing contracts, validated
prediction inputs, preserved model version/input data, commits, and rollback on a
database error using explicit mocks. Ruff was rerun afterward and passed.

Standard-library data/preprocessing tests can run without installing ML packages:

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_ml_data.py -v
```

After installing dependencies and training a model:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
$env:RUN_DB_TESTS = '1'
$env:RUN_ML_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:RUN_DB_TESTS, Env:RUN_ML_TESTS
cd ..
.\scripts\dev.ps1 check
```

The opt-in ML integration test performs real inference, verifies the persisted row, then
deletes its own test record. Unit tests use explicit mocks, not a replacement application
model. No synthetic fixture is used to train an artifact or present model metrics.

Design references: [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html)
and [Keras model loading](https://www.tensorflow.org/api_docs/python/tf/keras/models/load_model).
