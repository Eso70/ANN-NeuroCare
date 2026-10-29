# PostgreSQL and low-recall correction — 2026-10-27

## Current result

The original ANN weights and dataset were preserved. A new version selects its decision
cutoff using **validation data only**, maximizing F2 (with highest cutoff breaking ties).
This is an educational recall-oriented objective, not an agreed clinical utility function.
The test data is used only for reporting after selection. Future training uses the same
validation-only cutoff policy for the ANN and logistic baseline.

Active version: `artifacts/20261027T204111Z-db7cb83c`.
Parent version: `20261027T203103Z-5eefa372`.
The model SHA-256 and saved split indices are unchanged. Root `.env` selects the new
version; the parent artifact remains intact for reproducibility.

| Test result on the same saved partition | Original cutoff | Validation-selected cutoff |
| --- | ---: | ---: |
| Decision threshold | 0.5 | 0.128489 |
| Recall | 11.78% | 82.91% |
| Precision | 59.93% | 28.03% |
| Accuracy | 86.99% | 68.87% |
| Specificity | 98.77% | 66.67% |
| False negatives | 6,079 | 1,178 |
| False positives | 543 | 14,667 |

This detects many more positive dataset labels at the cost of many more false positives.
It does not improve the underlying ranking or establish clinical validity. The test
partition was already reported in Phase 3; this comparison is **not a fresh independent
validation**, although no test labels enter cutoff selection. Do not repeatedly adjust
the objective against these test results. New independent data is needed for such validation.

The API loads the saved threshold, uses it for classification, and returns it in each
prediction response as `decision_threshold`. The form displays that returned value and
the model's saved evaluation/precision, rather than hardcoded 0.5 or 50%. Model versions
remain persisted with every prediction so its cutoff can be traced to its artifact.

To reproduce cutoff selection from the existing frozen model, from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.ml.tune --model-dir ../artifacts/20261027T203103Z-5eefa372 --csv ../data/diabetes_binary_health_indicators_BRFSS2015.csv
```

This verifies dataset SHA-256, saved split coverage and profile disjointness, creates a
new version without retraining the ANN, records validation selection details and evaluates
the test partition. It never overwrites the parent model or changes MODEL_DIR automatically.

Method reference: [scikit-learn decision-threshold guidance](https://scikit-learn.org/stable/modules/classification_threshold.html).

## PostgreSQL correction

The local cluster serves IPv4 loopback. DATABASE_URL now uses `127.0.0.1` explicitly,
avoiding IPv6 localhost attempts. Credentials and database contents were preserved.
Background server lifetimes proved unreliable in the managed execution environment:
readiness checks could succeed, followed later by refused/timed-out connections.

A foreground server kept alive across the checks allowed migrations and real database
tests to succeed. The helper now offers `db-run` for that mode. `db-start` checks an
already-running cluster and refuses to launch another instance when the port is already
serving an unconfirmed PostgreSQL instance. No existing database is reinitialized.

For a reliable local demonstration, keep three PowerShell terminals open at the root:

```powershell
# Terminal 1: keep PostgreSQL attached to this terminal
.\scripts\dev.ps1 db-run
```

```powershell
# Terminal 2: migrations and API
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 backend
```

```powershell
# Terminal 3: browser app
.\scripts\dev.ps1 frontend
```

Open http://localhost:5173/predictions. If PostgreSQL is already running successfully,
reuse it instead of starting another server. Stop the project-local database cleanly
using `scripts/dev.ps1 db-stop`; avoid closing it forcibly.

## Executed verification

- Alembic upgrade succeeded against the real project PostgreSQL database.
- **39 backend tests passed, zero skipped**, with `RUN_DB_TESTS=1`, `RUN_ML_TESTS=1`,
  and `RUN_MODEL_TESTS=1`. This includes migrated-table verification, actual ANN loading,
  real prediction persistence/retrieval and cleanup, invalid inputs, missing model
  artifacts, threshold selection and threshold propagation.
- Frontend TypeScript/Vite production build and ESLint passed.
- Backend Ruff, Python source compilation and PowerShell helper parsing passed.
- Live HTTP smoke test against a temporary Uvicorn server passed: real database health,
  model metadata/contract, prediction creation and SQLAlchemy retrieval, CORS for the
  frontend origin, returned cutoff/class consistency, and 422 for an invalid age code.
  Its demonstration row was deleted and the temporary API server stopped afterward.
- A Starlette/AnyIO dependency deprecation warning remains; it did not fail any test.

These results supersede the earlier database-blocked reports in `verification.md`
and the original Phase 3 report. The wider university-demonstration review remains
a separate task; no authentication, history UI or unrelated features were added here.
